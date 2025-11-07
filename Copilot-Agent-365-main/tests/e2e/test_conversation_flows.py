"""
End-to-End tests for conversation flows

Tests cover:
- Complete conversation scenarios
- Multi-turn conversations
- Demo activation and progression
- Real-world usage patterns
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


@pytest.fixture
def mock_assistant():
    """Fixture to create a mock assistant for E2E tests"""
    with patch('function_app.AzureOpenAI'), \
         patch('function_app.AzureFileStorageManager') as mock_storage:

        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.list_files.return_value = []
        mock_storage_instance.set_memory_context = MagicMock()
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})
        assistant.storage_manager = mock_storage_instance
        assistant.client = MagicMock()

        yield assistant


class TestCompleteConversationFlow:
    """Test complete conversation scenarios"""

    def test_greeting_and_question_flow(self, mock_assistant):
        """Test basic greeting followed by question"""
        # Turn 1: Greeting
        mock_response1 = MockOpenAIResponse(
            content="Hello! How can I assist you today?|||VOICE|||Hey there, what can I help you with?"
        )
        mock_assistant.client.chat.completions.create.return_value = mock_response1

        formatted1, voice1, logs1 = mock_assistant.get_response("Hello", [])

        assert "Hello" in formatted1 or "assist" in formatted1
        assert voice1 != ""

        # Turn 2: Question with history
        conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": formatted1}
        ]

        mock_response2 = MockOpenAIResponse(
            content="I can help you with many tasks including memory management, drafting emails, and more.|||VOICE|||I can help with memory, emails, and lots more."
        )
        mock_assistant.client.chat.completions.create.return_value = mock_response2

        formatted2, voice2, logs2 = mock_assistant.get_response("What can you do?", conversation_history)

        assert "help" in formatted2.lower()
        assert voice2 != ""

    def test_information_storage_and_recall(self, mock_assistant):
        """Test storing information and recalling it"""
        from agents.manage_memory_agent import ManageMemoryAgent

        # Add ManageMemory agent
        memory_agent = ManageMemoryAgent()
        mock_assistant.known_agents = {'ManageMemory': memory_agent}

        # Turn 1: Store information
        mock_function_call = MockFunctionCall('ManageMemory', '{"fact": "User likes Python", "user_guid": "test-guid"}')
        mock_agent_response = MockOpenAIResponse(function_call=mock_function_call)
        mock_final_response = MockOpenAIResponse(
            content="I've stored that information.|||VOICE|||Got it, stored."
        )

        mock_assistant.client.chat.completions.create.side_effect = [
            mock_agent_response,
            mock_final_response
        ]

        formatted1, voice1, logs1 = mock_assistant.get_response("Remember that I like Python", [])

        assert "ManageMemory" in logs1
        assert formatted1 != ""

    def test_error_recovery_flow(self, mock_assistant):
        """Test conversation continues after error"""
        # Turn 1: Error occurs
        mock_assistant.client.chat.completions.create.side_effect = Exception("Temporary error")

        formatted1, voice1, logs1 = mock_assistant.get_response("Test message", [])

        # Should return error message
        assert "error" in formatted1.lower() or "unavailable" in formatted1.lower()

        # Turn 2: Recovery - service works again
        conversation_history = [
            {"role": "user", "content": "Test message"},
            {"role": "assistant", "content": formatted1}
        ]

        mock_response = MockOpenAIResponse(
            content="I'm back and working now!|||VOICE|||I'm working now."
        )
        mock_assistant.client.chat.completions.create.side_effect = None
        mock_assistant.client.chat.completions.create.return_value = mock_response

        formatted2, voice2, logs2 = mock_assistant.get_response("Are you working now?", conversation_history)

        assert formatted2 != ""
        assert "error" not in formatted2.lower()


class TestMultiTurnConversation:
    """Test multi-turn conversation scenarios"""

    def test_context_maintained_across_turns(self, mock_assistant):
        """Test that context is maintained across multiple turns"""
        conversation_history = []

        # Turn 1
        mock_response1 = MockOpenAIResponse(content="My name is Assistant.|||VOICE|||I'm Assistant.")
        mock_assistant.client.chat.completions.create.return_value = mock_response1

        formatted1, voice1, logs1 = mock_assistant.get_response("What's your name?", conversation_history)

        conversation_history.extend([
            {"role": "user", "content": "What's your name?"},
            {"role": "assistant", "content": formatted1}
        ])

        # Turn 2 - Should remember context
        mock_response2 = MockOpenAIResponse(content="I just told you, I'm Assistant.|||VOICE|||I'm Assistant, like I said.")
        mock_assistant.client.chat.completions.create.return_value = mock_response2

        formatted2, voice2, logs2 = mock_assistant.get_response("What was your name again?", conversation_history)

        assert formatted2 != ""

        # Verify history was passed correctly
        call_args = mock_assistant.client.chat.completions.create.call_args
        messages = call_args.kwargs.get('messages') or call_args[1].get('messages')
        assert len(messages) >= 3  # System + 2 previous messages + current

    def test_long_conversation_history(self, mock_assistant):
        """Test conversation with long history"""
        # Create a long conversation history
        conversation_history = []
        for i in range(10):
            conversation_history.extend([
                {"role": "user", "content": f"Message {i}"},
                {"role": "assistant", "content": f"Response {i}"}
            ])

        mock_response = MockOpenAIResponse(content="Still working!|||VOICE|||Still here.")
        mock_assistant.client.chat.completions.create.return_value = mock_response

        formatted, voice, logs = mock_assistant.get_response("Are you still there?", conversation_history)

        assert formatted != ""
        assert voice != ""


class TestDemoActivationAndProgression:
    """Test demo activation and progression"""

    def test_demo_trigger_activation(self, mock_assistant):
        """Test that demo trigger activates demo"""
        # Mock demo file
        demo_data = {
            "trigger_phrases": ["start sales demo"],
            "conversation_flow": [
                {"user_message": "start sales demo", "bot_response": "Welcome to sales demo!"},
                {"user_message": "next", "bot_response": "Here's step 2"}
            ]
        }

        mock_file = MagicMock()
        mock_file.name = 'sales_demo.json'
        mock_assistant.storage_manager.list_files.return_value = [mock_file]
        mock_assistant.storage_manager.read_file.return_value = json.dumps(demo_data)

        # Add ScriptedDemo agent
        mock_scripted_agent = MagicMock()
        mock_scripted_agent.perform.return_value = "Welcome to sales demo!"
        mock_assistant.known_agents = {'ScriptedDemo': mock_scripted_agent}

        formatted, voice, logs = mock_assistant.get_response("start sales demo", [])

        assert "sales_demo" in logs
        assert "Welcome" in formatted

    def test_demo_progression(self, mock_assistant):
        """Test progressing through demo steps"""
        demo_data = {
            "conversation_flow": [
                {"user_message": "start demo", "bot_response": "Step 1"},
                {"user_message": "next", "bot_response": "Step 2"},
                {"user_message": "next", "bot_response": "Step 3"}
            ]
        }

        mock_file = MagicMock()
        mock_file.name = 'test_demo.json'
        mock_assistant.storage_manager.list_files.return_value = [mock_file]
        mock_assistant.storage_manager.read_file.return_value = json.dumps(demo_data)

        # Mock ScriptedDemo agent
        mock_scripted_agent = MagicMock()
        mock_scripted_agent.perform.side_effect = ["Step 1", "Step 2", "Step 3"]
        mock_assistant.known_agents = {'ScriptedDemo': mock_scripted_agent}

        # Step 1 - Trigger
        conversation_history = []
        formatted1, voice1, logs1 = mock_assistant.get_response("start demo", conversation_history)
        assert "Step 1" in logs1

        # Step 2 - Continue
        conversation_history.extend([
            {"role": "user", "content": "start demo"},
            {"role": "system", "content": logs1},
            {"role": "assistant", "content": formatted1}
        ])
        formatted2, voice2, logs2 = mock_assistant.get_response("next", conversation_history)
        assert "Step 2" in logs2 or "Step 2" in formatted2

    def test_demo_exit(self, mock_assistant):
        """Test exiting an active demo"""
        # Setup active demo in history
        conversation_history = [
            {"role": "user", "content": "start demo"},
            {"role": "system", "content": "Performed TestDemo and got result: Step 1 of 3"}
        ]

        formatted, voice, logs = mock_assistant.get_response("exit demo", conversation_history)

        assert "DemoExit" in logs or "help" in formatted.lower()


class TestRealWorldScenarios:
    """Test real-world usage patterns"""

    def test_new_user_session_initialization(self, mock_assistant):
        """Test new user session with GUID"""
        new_user_guid = "new-user-1111-2222-3333-444444444444"

        # Mock context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "New user memory initialized"
        mock_assistant.known_agents = {'ContextMemory': mock_context_agent}

        mock_response = MockOpenAIResponse(
            content="Welcome! I've loaded your memory.|||VOICE|||Welcome, memory loaded."
        )
        mock_assistant.client.chat.completions.create.return_value = mock_response

        # First message is GUID only
        formatted, voice, logs = mock_assistant.get_response(new_user_guid, [])

        assert mock_assistant.user_guid == new_user_guid
        assert "loaded" in formatted.lower() or "memory" in formatted.lower()

    def test_returning_user_session(self, mock_assistant):
        """Test returning user with existing memory"""
        returning_user_guid = "existing-user-5555-6666-7777-888888888888"

        # Mock existing memory
        mock_assistant.storage_manager.read_json.return_value = {
            "memory1": {"content": "User previously mentioned Python"}
        }

        # Mock context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "User previously mentioned Python"
        mock_assistant.known_agents = {'ContextMemory': mock_context_agent}

        mock_response = MockOpenAIResponse(
            content="Welcome back! I remember you like Python.|||VOICE|||Welcome back, Python fan."
        )
        mock_assistant.client.chat.completions.create.return_value = mock_response

        conversation_history = [
            {"role": "user", "content": returning_user_guid}
        ]

        formatted, voice, logs = mock_assistant.get_response("I'm back!", conversation_history)

        assert mock_assistant.user_guid == returning_user_guid

    def test_anonymous_user_with_default_guid(self, mock_assistant):
        """Test anonymous user gets default GUID"""
        mock_response = MockOpenAIResponse(
            content="Hello! How can I help?|||VOICE|||Hey, what's up?"
        )
        mock_assistant.client.chat.completions.create.return_value = mock_response

        formatted, voice, logs = mock_assistant.get_response("Hello", [])

        # Should use default GUID
        assert mock_assistant.user_guid == DEFAULT_USER_GUID

    def test_conversation_with_special_characters(self, mock_assistant):
        """Test conversation with special characters and formatting"""
        mock_response = MockOpenAIResponse(
            content="Sure! Here's code: `print('Hello')`|||VOICE|||Here's the code."
        )
        mock_assistant.client.chat.completions.create.return_value = mock_response

        formatted, voice, logs = mock_assistant.get_response("Show me Python code", [])

        assert "print" in formatted
        assert "`" in formatted  # Code formatting preserved

    def test_concurrent_user_sessions(self, mock_assistant):
        """Test that different users maintain separate contexts"""
        user1_guid = "user1-0000-1111-2222-333333333333"
        user2_guid = "user2-4444-5555-6666-777777777777"

        # Mock context memory
        mock_context_agent = MagicMock()
        mock_context_agent.perform.side_effect = ["User 1 memory", "User 2 memory"]
        mock_assistant.known_agents = {'ContextMemory': mock_context_agent}

        mock_response = MockOpenAIResponse(content="Response|||VOICE|||Voice")
        mock_assistant.client.chat.completions.create.return_value = mock_response

        # User 1 session
        mock_assistant._initialize_context_memory(user1_guid)
        assert mock_assistant.user_guid == user1_guid

        # User 2 session
        mock_assistant._initialize_context_memory(user2_guid)
        assert mock_assistant.user_guid == user2_guid

        # Verify context switching occurred
        assert mock_assistant.storage_manager.set_memory_context.call_count >= 2
