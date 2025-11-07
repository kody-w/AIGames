"""
Unit tests for memory context and GUID handling

Tests cover:
- GUID extraction from user input
- Memory context initialization
- User context switching
- Demo trigger detection
- Demo state extraction
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import re

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from function_app import Assistant, DEFAULT_USER_GUID


class TestGUIDExtraction:
    """Test cases for GUID extraction functionality"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def setup_assistant(self, mock_storage, mock_openai):
        """Helper to create assistant instance"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})
        return assistant

    def test_extract_valid_guid(self):
        """Test extracting valid GUID from text"""
        assistant = self.setup_assistant()

        valid_guid = "12345678-1234-1234-1234-123456789abc"
        result = assistant.extract_user_guid(valid_guid)

        assert result == valid_guid

    def test_extract_guid_with_whitespace(self):
        """Test extracting GUID with surrounding whitespace"""
        assistant = self.setup_assistant()

        guid_with_space = "  12345678-1234-1234-1234-123456789abc  "
        result = assistant.extract_user_guid(guid_with_space)

        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_extract_labeled_guid(self):
        """Test extracting GUID with label prefix"""
        assistant = self.setup_assistant()

        labeled_guid = "guid: 12345678-1234-1234-1234-123456789abc"
        result = assistant.extract_user_guid(labeled_guid)

        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_extract_guid_with_equals(self):
        """Test extracting GUID with equals sign"""
        assistant = self.setup_assistant()

        labeled_guid = "guid=12345678-1234-1234-1234-123456789abc"
        result = assistant.extract_user_guid(labeled_guid)

        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_no_guid_in_text(self):
        """Test that non-GUID text returns None"""
        assistant = self.setup_assistant()

        result = assistant.extract_user_guid("This is just regular text")

        assert result is None

    def test_guid_embedded_in_sentence(self):
        """Test that GUID embedded in sentence is not extracted"""
        assistant = self.setup_assistant()

        text = "My GUID is 12345678-1234-1234-1234-123456789abc for this session"
        result = assistant.extract_user_guid(text)

        assert result is None  # Should not extract if not entire message

    def test_invalid_guid_format(self):
        """Test that invalid GUID format returns None"""
        assistant = self.setup_assistant()

        invalid_guids = [
            "12345678-1234-1234-1234",  # Too short
            "12345678-1234-1234-1234-123456789abcdef",  # Too long
            "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # Invalid characters
            "12345678_1234_1234_1234_123456789abc"  # Wrong delimiter
        ]

        for invalid in invalid_guids:
            result = assistant.extract_user_guid(invalid)
            assert result is None

    def test_none_input(self):
        """Test that None input returns None"""
        assistant = self.setup_assistant()

        result = assistant.extract_user_guid(None)

        assert result is None

    def test_check_first_message_for_guid(self):
        """Test checking first message in conversation history for GUID"""
        assistant = self.setup_assistant()

        valid_guid = "12345678-1234-1234-1234-123456789abc"
        conversation_history = [
            {"role": "user", "content": valid_guid}
        ]

        result = assistant._check_first_message_for_guid(conversation_history)

        assert result == valid_guid

    def test_check_first_message_not_guid(self):
        """Test that non-GUID first message returns None"""
        assistant = self.setup_assistant()

        conversation_history = [
            {"role": "user", "content": "Hello, how are you?"}
        ]

        result = assistant._check_first_message_for_guid(conversation_history)

        assert result is None

    def test_check_empty_conversation_history(self):
        """Test empty conversation history returns None"""
        assistant = self.setup_assistant()

        result = assistant._check_first_message_for_guid([])

        assert result is None


class TestMemoryContextInitialization:
    """Test cases for memory context initialization"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_initialize_with_default_guid(self, mock_storage, mock_openai):
        """Test that assistant initializes with default GUID"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        assert assistant.user_guid == DEFAULT_USER_GUID

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_initialize_context_memory_called(self, mock_storage, mock_openai):
        """Test that context memory initialization is called"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage_instance.set_memory_context = MagicMock()
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        # Verify set_memory_context was called
        assert mock_storage_instance.set_memory_context.called

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_context_switch_updates_memory(self, mock_storage, mock_openai):
        """Test that switching context updates memory"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        new_guid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

        # Mock the context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "Context memory loaded"
        assistant.known_agents = {'ContextMemory': mock_context_agent}

        # Initialize with new GUID
        assistant._initialize_context_memory(new_guid)

        # Verify set_memory_context was called with new GUID
        mock_storage_instance.set_memory_context.assert_called()


class TestDemoTriggerDetection:
    """Test cases for demo trigger detection"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def setup_assistant_with_demo(self, mock_storage, mock_openai):
        """Helper to create assistant with demo data"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.side_effect = lambda share, filename: {
            ('demos', 'test_demo.json'): '{"trigger_phrases": ["start demo", "begin demo"], "conversation_flow": [{"step": 1, "response": "Demo started"}]}'
        }.get((share, filename))

        mock_file = MagicMock()
        mock_file.name = 'test_demo.json'
        mock_storage_instance.list_files.return_value = [mock_file]
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})
        return assistant

    def test_detect_demo_trigger(self):
        """Test detecting demo trigger phrase"""
        assistant = self.setup_assistant_with_demo()

        result = assistant.check_demo_trigger("start demo")

        assert result['triggered'] is True
        assert 'demo_name' in result
        assert 'conversation_flow' in result

    def test_no_demo_trigger(self):
        """Test that non-trigger phrase doesn't activate demo"""
        assistant = self.setup_assistant_with_demo()

        result = assistant.check_demo_trigger("hello there")

        assert result['triggered'] is False

    def test_case_insensitive_trigger(self):
        """Test that demo trigger is case insensitive"""
        assistant = self.setup_assistant_with_demo()

        result = assistant.check_demo_trigger("START DEMO")

        assert result['triggered'] is True

    def test_trigger_with_whitespace(self):
        """Test demo trigger with extra whitespace"""
        assistant = self.setup_assistant_with_demo()

        result = assistant.check_demo_trigger("  start demo  ")

        assert result['triggered'] is True


class TestDemoStateExtraction:
    """Test cases for demo state extraction from history"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def setup_assistant(self, mock_storage, mock_openai):
        """Helper to create assistant instance"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.side_effect = lambda share, filename: '{"conversation_flow": [{"step": 1}, {"step": 2}, {"step": 3}]}'
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})
        return assistant

    def test_extract_demo_state_from_history(self):
        """Test extracting active demo state from conversation"""
        assistant = self.setup_assistant()

        conversation_history = [
            {"role": "user", "content": "start demo"},
            {"role": "system", "content": "Performed TestDemo and got result: Step 1 of 3"}
        ]

        demo_name, current_step, demo_steps = assistant._extract_demo_state_from_history(conversation_history)

        assert demo_name == "TestDemo"
        assert current_step == 1
        assert demo_steps is not None

    def test_extract_no_demo_from_empty_history(self):
        """Test that empty history returns no demo state"""
        assistant = self.setup_assistant()

        demo_name, current_step, demo_steps = assistant._extract_demo_state_from_history([])

        assert demo_name is None
        assert current_step == 0
        assert demo_steps is None

    def test_extract_demo_completion_state(self):
        """Test that completed demo is detected"""
        assistant = self.setup_assistant()

        conversation_history = [
            {"role": "system", "content": "Performed TestDemo and got result: Step 3 of 3"},
            {"role": "system", "content": "Performed DemoCompletion and got result: TestDemo finished"}
        ]

        demo_name, current_step, demo_steps = assistant._extract_demo_state_from_history(conversation_history)

        assert demo_name is None  # Demo completed
        assert current_step == 0
        assert demo_steps is None


class TestMemoryContextSwitching:
    """Test cases for user context switching"""

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_context_switches_on_new_guid(self, mock_storage, mock_openai):
        """Test that context switches when new GUID is provided"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})
        original_guid = assistant.user_guid

        # Mock context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "Memory loaded"
        assistant.known_agents = {'ContextMemory': mock_context_agent}

        new_guid = "new-guid-0000-1111-2222-333333333333"
        assistant._initialize_context_memory(new_guid)

        # Verify storage context was switched
        assert mock_storage_instance.set_memory_context.called

    @patch('function_app.AzureOpenAI')
    @patch('function_app.AzureFileStorageManager')
    def test_default_guid_used_when_none_provided(self, mock_storage, mock_openai):
        """Test that default GUID is used when none provided"""
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = None
        mock_storage.return_value = mock_storage_instance

        assistant = Assistant({})

        # Mock context memory agent
        mock_context_agent = MagicMock()
        mock_context_agent.perform.return_value = "Memory loaded"
        assistant.known_agents = {'ContextMemory': mock_context_agent}

        # Initialize with None (should use default)
        assistant._initialize_context_memory(None)

        # Should have default GUID
        assert assistant.user_guid == DEFAULT_USER_GUID
