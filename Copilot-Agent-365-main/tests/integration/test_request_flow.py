"""
Integration tests for full request flow

Tests cover:
- Complete request processing pipeline
- Agent execution with mock OpenAI
- Memory read/write operations
- User context switching
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, MagicMock, patch

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from function_app import Assistant, DEFAULT_USER_GUID
from agents.basic_agent import BasicAgent


class TestAgent(BasicAgent):
    """Test agent for integration tests"""
    def __init__(self):
        self.name = 'TestAgent'
        self.metadata = {
            "name": self.name,
            "description": "Test agent for integration testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action to perform"
                    }
                },
                "required": ["action"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        action = kwargs.get('action', '')
        return f"Performed action: {action}"


class MockOpenAIResponse:
    """Mock OpenAI API response"""
    def __init__(self, content=None, function_call=None):
        self.choices = [MagicMock()]
        self.choices[0].message = MagicMock()
        self.choices[0].message.content = content
        self.choices[0].message.function_call = function_call


class MockFunctionCall:
    """Mock function call object"""
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class TestFullRequestFlow:
    """Test cases for full request processing"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def setup_assistant_with_agent(self, mock_storage, mock_openai):
        """Helper to create assistant with test agent"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage_instance.set_memory_context = MagicMock()
        mock_storage.return_value = mock_storage_instance

        test_agent = TestAgent()
        agents = {'TestAgent': test_agent}

        assistant = Assistant(agents)
        assistant.storage_manager = mock_storage_instance

        return assistant, mock_storage_instance, mock_openai

    def test_simple_conversation_without_agent(self):
        """Test simple conversation that doesn't trigger agents"""
        assistant, mock_storage, mock_openai = self.setup_assistant_with_agent()

        # Mock OpenAI to return simple response
        mock_response = MockOpenAIResponse(content="Hello! How can I help you?|||VOICE|||Hey there, what can I do for you?")
        assistant.client = MagicMock()
        assistant.client.chat.completions.create.return_value = mock_response

        formatted, voice, logs = assistant.get_response("Hello", [])

        assert "Hello" in formatted or "help" in formatted
        assert voice != ""
        assert logs == ""  # No agent calls

    def test_conversation_with_agent_call(self):
        """Test conversation that triggers agent execution"""
        assistant, mock_storage, mock_openai = self.setup_assistant_with_agent()

        # Mock OpenAI to first call agent, then return final response
        mock_function_call = MockFunctionCall('TestAgent', '{"action": "test_action"}')
        mock_agent_response = MockOpenAIResponse(function_call=mock_function_call)
        mock_final_response = MockOpenAIResponse(content="I've performed the action|||VOICE|||Done!")

        assistant.client = MagicMock()
        assistant.client.chat.completions.create.side_effect = [
            mock_agent_response,
            mock_final_response
        ]

        formatted, voice, logs = assistant.get_response("Do something", [])

        assert "TestAgent" in logs
        assert "test_action" in logs
        assert formatted != ""
        assert voice != ""

    def test_multiple_turns_conversation(self):
        """Test multi-turn conversation flow"""
        assistant, mock_storage, mock_openai = self.setup_assistant_with_agent()

        # Mock OpenAI responses
        mock_response1 = MockOpenAIResponse(content="First response|||VOICE|||First")
        mock_response2 = MockOpenAIResponse(content="Second response|||VOICE|||Second")

        assistant.client = MagicMock()
        assistant.client.chat.completions.create.side_effect = [
            mock_response1,
            mock_response2
        ]

        # First turn
        formatted1, voice1, logs1 = assistant.get_response("First message", [])
        assert "First" in formatted1

        # Second turn with history
        conversation_history = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": formatted1}
        ]
        formatted2, voice2, logs2 = assistant.get_response("Second message", conversation_history)
        assert "Second" in formatted2

    def test_error_handling_in_request_flow(self):
        """Test error handling during request processing"""
        assistant, mock_storage, mock_openai = self.setup_assistant_with_agent()

        # Mock OpenAI to raise exception
        assistant.client = MagicMock()
        assistant.client.chat.completions.create.side_effect = Exception("API Error")

        # Should handle error gracefully with retries
        formatted, voice, logs = assistant.get_response("Test message", [])

        # Should return error message
        assert "error" in formatted.lower() or "unavailable" in formatted.lower()


class TestMemoryOperations:
    """Test cases for memory read/write operations"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_memory_read_operation(self, mock_storage, mock_openai):
        """Test reading from memory storage"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_json.return_value = {
            "memory1": {"content": "Test memory"}
        }
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        # Verify storage read was called during initialization
        assert mock_storage_instance.read_json.called or mock_storage_instance.read_file.called

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_memory_write_operation(self, mock_storage, mock_openai):
        """Test writing to memory storage"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage_instance.write_json = MagicMock()
        mock_storage.return_value = mock_storage_instance

        # Create ManageMemory agent
        from agents.manage_memory_agent import ManageMemoryAgent
        manage_agent = ManageMemoryAgent()

        # Perform memory write
        result = manage_agent.perform(
            fact="Test fact",
            user_guid="test-guid-1234"
        )

        # Should have interacted with storage
        assert "stored" in result.lower() or "saved" in result.lower() or "added" in result.lower()


class TestUserContextSwitching:
    """Test cases for user context switching during requests"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_context_switch_on_guid_input(self, mock_storage, mock_openai):
        """Test that context switches when GUID is provided"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        # Mock context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "Memory loaded"
        assistant.known_agents = {'ContextMemory': mock_context_agent}

        # Mock OpenAI response
        mock_response = MockOpenAIResponse(content="Context loaded|||VOICE|||Loaded")
        assistant.client = MagicMock()
        assistant.client.chat.completions.create.return_value = mock_response

        new_guid = "12345678-1234-1234-1234-123456789abc"

        # Make request with GUID
        formatted, voice, logs = assistant.get_response(new_guid, [])

        # Verify context was switched
        assert assistant.user_guid == new_guid
        assert mock_storage_instance.set_memory_context.called

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_default_guid_used_without_input(self, mock_storage, mock_openai):
        """Test that default GUID is used when none provided"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        # Should have default GUID
        assert assistant.user_guid == DEFAULT_USER_GUID

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_guid_from_conversation_history(self, mock_storage, mock_openai):
        """Test GUID extraction from conversation history"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        # Mock context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "Memory loaded"
        assistant.known_agents = {'ContextMemory': mock_context_agent}

        # Mock OpenAI
        mock_response = MockOpenAIResponse(content="Response|||VOICE|||Voice")
        assistant.client = MagicMock()
        assistant.client.chat.completions.create.return_value = mock_response

        test_guid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        conversation_history = [
            {"role": "user", "content": test_guid}
        ]

        formatted, voice, logs = assistant.get_response("Hello", conversation_history)

        # GUID should be extracted from history
        assert assistant.user_guid == test_guid


class TestAgentExecution:
    """Test cases for agent execution pipeline"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_agent_parameter_sanitization(self, mock_storage, mock_openai):
        """Test that agent parameters are sanitized"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        test_agent = TestAgent()
        assistant = Assistant({'TestAgent': test_agent})

        # Mock function call with None parameter
        mock_function_call = MockFunctionCall('TestAgent', '{"action": null}')
        mock_agent_response = MockOpenAIResponse(function_call=mock_function_call)
        mock_final_response = MockOpenAIResponse(content="Done|||VOICE|||Done")

        assistant.client = MagicMock()
        assistant.client.chat.completions.create.side_effect = [
            mock_agent_response,
            mock_final_response
        ]

        formatted, voice, logs = assistant.get_response("Test", [])

        # Should handle None parameter gracefully
        assert "TestAgent" in logs

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_nonexistent_agent_handling(self, mock_storage, mock_openai):
        """Test handling of calls to non-existent agents"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})  # No agents

        # Mock function call to non-existent agent
        mock_function_call = MockFunctionCall('NonExistentAgent', '{"param": "value"}')
        mock_response = MockOpenAIResponse(function_call=mock_function_call)

        assistant.client = MagicMock()
        assistant.client.chat.completions.create.return_value = mock_response

        formatted, voice, logs = assistant.get_response("Test", [])

        # Should handle gracefully
        assert "not exist" in formatted.lower() or "nonexistentagent" in formatted.lower()


class TestResponseParsing:
    """Test cases for response parsing and formatting"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_parse_response_with_voice_delimiter(self, mock_storage, mock_openai):
        """Test parsing response with voice delimiter"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        formatted, voice = assistant.parse_response_with_voice(
            "This is the formatted response|||VOICE|||This is the voice"
        )

        assert formatted == "This is the formatted response"
        assert voice == "This is the voice"

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_parse_response_without_voice_delimiter(self, mock_storage, mock_openai):
        """Test parsing response without voice delimiter"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        formatted, voice = assistant.parse_response_with_voice(
            "This is a response without voice delimiter."
        )

        assert formatted == "This is a response without voice delimiter."
        assert voice != ""  # Should generate a voice response
        assert len(voice) > 0
