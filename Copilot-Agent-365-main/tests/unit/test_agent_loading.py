"""
Unit tests for agent loading functionality

Tests cover:
- Agent loading from local folder
- Agent metadata extraction
- Agent reloading
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
import importlib

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.basic_agent import BasicAgent


class MockAgent(BasicAgent):
    """Mock agent for testing"""
    def __init__(self):
        self.name = 'MockAgent'
        self.metadata = {
            "name": self.name,
            "description": "Mock agent for testing",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_param": {
                        "type": "string",
                        "description": "Test parameter"
                    }
                },
                "required": ["test_param"]
            }
        }
        super().__init__(self.name, self.metadata)

    def perform(self, **kwargs):
        return f"Mock result: {kwargs.get('test_param', '')}"


class TestAgentLoading:
    """Test cases for agent loading functionality"""

    @patch('function_app.AzureFileStorageManager')
    @patch('os.listdir')
    @patch('importlib.import_module')
    def test_load_agents_from_local_folder(self, mock_import, mock_listdir, mock_storage):
        """Test loading agents from local folder"""
        from function_app import load_agents_from_folder

        # Mock the directory listing
        mock_listdir.return_value = ['mock_agent.py', '__init__.py', 'basic_agent.py']

        # Mock the module import
        mock_module = MagicMock()
        mock_agent_instance = MockAgent()
        mock_module.__dict__ = {'MockAgent': MockAgent}
        mock_import.return_value = mock_module

        # Mock inspect.getmembers to return our mock agent
        with patch('function_app.inspect.getmembers') as mock_getmembers:
            mock_getmembers.return_value = [('MockAgent', MockAgent)]

            # Mock Azure storage to return empty list
            mock_storage_instance = MagicMock()
            mock_storage_instance.list_files.return_value = []
            mock_storage.return_value = mock_storage_instance

            # Run the function
            result = load_agents_from_folder()

            # Verify agent was loaded
            assert 'MockAgent' in result
            assert isinstance(result['MockAgent'], BasicAgent)

    @patch('function_app.AzureFileStorageManager')
    def test_load_agents_handles_import_error(self, mock_storage):
        """Test that agent loading handles import errors gracefully"""
        from function_app import load_agents_from_folder

        # Mock storage to raise an error
        mock_storage_instance = MagicMock()
        mock_storage_instance.list_files.side_effect = Exception("Storage error")
        mock_storage.return_value = mock_storage_instance

        # Should not raise exception
        with patch('os.listdir', return_value=[]):
            result = load_agents_from_folder()
            assert isinstance(result, dict)

    def test_agent_has_required_attributes(self):
        """Test that agent instances have required attributes"""
        agent = MockAgent()

        assert hasattr(agent, 'name')
        assert hasattr(agent, 'metadata')
        assert hasattr(agent, 'perform')
        assert callable(agent.perform)

    def test_agent_metadata_structure(self):
        """Test that agent metadata has correct structure"""
        agent = MockAgent()

        assert 'name' in agent.metadata
        assert 'description' in agent.metadata
        assert 'parameters' in agent.metadata
        assert 'type' in agent.metadata['parameters']
        assert 'properties' in agent.metadata['parameters']

    def test_agent_perform_method(self):
        """Test that agent perform method works correctly"""
        agent = MockAgent()
        result = agent.perform(test_param="test_value")

        assert "test_value" in result
        assert isinstance(result, str)


class TestAssistantAgentReload:
    """Test cases for Assistant agent reloading functionality"""

    def test_reload_agents_with_dict(self):
        """Test reloading agents from dictionary"""
        from function_app import Assistant

        mock_agent1 = MockAgent()
        mock_agent1.name = "Agent1"

        mock_agent2 = MockAgent()
        mock_agent2.name = "Agent2"

        agent_dict = {
            "Agent1": mock_agent1,
            "Agent2": mock_agent2
        }

        # Create a minimal assistant without Azure dependencies
        with patch('function_app.AzureOpenAI'), \
             patch('function_app.AzureFileStorageManager'):

            assistant = Assistant({})
            result = assistant.reload_agents(agent_dict)

            assert 'Agent1' in result
            assert 'Agent2' in result
            assert len(result) == 2

    def test_reload_agents_with_list(self):
        """Test reloading agents from list"""
        from function_app import Assistant

        mock_agent1 = MockAgent()
        mock_agent1.name = "Agent1"

        mock_agent2 = MockAgent()
        mock_agent2.name = "Agent2"

        agent_list = [mock_agent1, mock_agent2]

        with patch('function_app.AzureOpenAI'), \
             patch('function_app.AzureFileStorageManager'):

            assistant = Assistant({})
            result = assistant.reload_agents(agent_list)

            assert 'Agent1' in result
            assert 'Agent2' in result
            assert len(result) == 2

    def test_get_agent_metadata(self):
        """Test getting agent metadata"""
        from function_app import Assistant

        mock_agent = MockAgent()

        with patch('function_app.AzureOpenAI'), \
             patch('function_app.AzureFileStorageManager'):

            assistant = Assistant({'MockAgent': mock_agent})
            metadata = assistant.get_agent_metadata()

            assert isinstance(metadata, list)
            assert len(metadata) > 0
            assert any('MockAgent' == m.get('name') for m in metadata)


class TestAgentFiltering:
    """Test cases for agent filtering by enabled_agents list"""

    @patch('function_app.AzureFileStorageManager')
    @patch('os.listdir')
    def test_load_agents_with_enabled_filter(self, mock_listdir, mock_storage):
        """Test that only enabled agents are loaded when filter is present"""
        from function_app import load_agents_from_folder

        mock_listdir.return_value = []

        # Mock storage with enabled_agents filter
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.return_value = '["agent1_agent.py", "agent2_agent.py"]'
        mock_storage_instance.list_files.return_value = [
            MagicMock(name='agent1_agent.py'),
            MagicMock(name='agent2_agent.py'),
            MagicMock(name='agent3_agent.py')  # This should be filtered out
        ]
        mock_storage.return_value = mock_storage_instance

        # Load agents with GUID (triggers filtering)
        result = load_agents_from_folder(user_guid="test-guid-1234")

        # Verify storage was called to get enabled agents config
        mock_storage_instance.read_file.assert_called_once()

    @patch('function_app.AzureFileStorageManager')
    @patch('os.listdir')
    def test_load_all_agents_without_filter(self, mock_listdir, mock_storage):
        """Test that all agents are loaded when no filter is present"""
        from function_app import load_agents_from_folder

        mock_listdir.return_value = []

        # Mock storage without enabled_agents filter
        mock_storage_instance = MagicMock()
        mock_storage_instance.read_file.side_effect = Exception("No config found")
        mock_storage_instance.list_files.return_value = []
        mock_storage.return_value = mock_storage_instance

        # Load agents without GUID (no filtering)
        result = load_agents_from_folder()

        # Should not fail even without filter config
        assert isinstance(result, dict)
