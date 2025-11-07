"""
Pytest configuration and shared fixtures for AI Ambassador Platform tests

This file contains fixtures that are shared across all test files.
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


@pytest.fixture
def mock_azure_storage():
    """
    Fixture to mock Azure Storage Manager

    Returns a MagicMock that simulates AzureFileStorageManager behavior
    """
    with patch('function_app.AzureFileStorageManager') as mock:
        mock_instance = MagicMock()
        mock_instance.read_file.return_value = None
        mock_instance.read_json.return_value = {}
        mock_instance.write_json.return_value = True
        mock_instance.write_file.return_value = True
        mock_instance.list_files.return_value = []
        mock_instance.set_memory_context.return_value = True
        mock_instance.ensure_directory_exists.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_openai():
    """
    Fixture to mock Azure OpenAI client

    Returns a MagicMock that simulates AzureOpenAI client behavior
    """
    with patch('function_app.AzureOpenAI') as mock:
        mock_instance = MagicMock()
        mock_instance.chat.completions.create.return_value = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_environment():
    """
    Fixture to mock environment variables

    Sets up required environment variables for testing
    """
    env_vars = {
        'AZURE_OPENAI_API_KEY': 'test-api-key',
        'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com/',
        'AZURE_OPENAI_DEPLOYMENT_NAME': 'gpt-4-test',
        'AZURE_OPENAI_API_VERSION': '2025-01-01-preview',
        'AzureWebJobsStorage': 'DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=testkey==;EndpointSuffix=core.windows.net',
        'AZURE_FILES_SHARE_NAME': 'test-share',
        'ASSISTANT_NAME': 'Test Assistant',
        'CHARACTERISTIC_DESCRIPTION': 'Test assistant for testing'
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def sample_conversation_history():
    """
    Fixture providing sample conversation history

    Returns a list of conversation messages for testing
    """
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "What can you do?"},
        {"role": "assistant", "content": "I can help with many tasks!"}
    ]


@pytest.fixture
def sample_agent_metadata():
    """
    Fixture providing sample agent metadata

    Returns agent metadata in OpenAI function format
    """
    return {
        "name": "TestAgent",
        "description": "A test agent for testing purposes",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform"
                },
                "data": {
                    "type": "string",
                    "description": "Data for the action"
                }
            },
            "required": ["action"]
        }
    }


@pytest.fixture
def sample_demo_data():
    """
    Fixture providing sample demo data

    Returns demo configuration with trigger phrases and conversation flow
    """
    return {
        "demo_name": "Sample Demo",
        "trigger_phrases": ["start demo", "begin demo"],
        "conversation_flow": [
            {
                "step": 1,
                "user_message": "start demo",
                "bot_response": "Welcome to the demo! This is step 1."
            },
            {
                "step": 2,
                "user_message": "next",
                "bot_response": "This is step 2 of the demo."
            },
            {
                "step": 3,
                "user_message": "continue",
                "bot_response": "Final step! Demo complete."
            }
        ]
    }


@pytest.fixture
def sample_ambassador_config():
    """
    Fixture providing sample ambassador configuration

    Returns ambassador JSON config for testing
    """
    return {
        "ambassador": {
            "id": "test-ambassador-001",
            "name": "Test Ambassador",
            "avatar": {
                "type": "emoji",
                "value": "🤖"
            },
            "world": {
                "type": "test_world",
                "environment": {
                    "theme": "technology"
                }
            },
            "agent_mapping": {
                "base_agent": "BasicAgent",
                "custom_agent": "TestAgent"
            },
            "demo_configuration": {
                "seeded_run": False,
                "parameters": {}
            }
        }
    }


@pytest.fixture
def sample_memory_data():
    """
    Fixture providing sample memory data

    Returns memory entries for testing
    """
    return {
        "memory1": {
            "id": "memory1",
            "content": "User prefers Python programming",
            "timestamp": "2025-01-01T12:00:00Z",
            "type": "preference"
        },
        "memory2": {
            "id": "memory2",
            "content": "User works in software development",
            "timestamp": "2025-01-01T12:05:00Z",
            "type": "fact"
        },
        "memory3": {
            "id": "memory3",
            "content": "User asked about Azure Functions",
            "timestamp": "2025-01-01T12:10:00Z",
            "type": "interaction"
        }
    }


@pytest.fixture
def valid_guids():
    """
    Fixture providing valid test GUIDs

    Returns a list of valid GUID strings for testing
    """
    return [
        "12345678-1234-1234-1234-123456789abc",
        "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "00000000-0000-0000-0000-000000000000",
        "ffffffff-ffff-ffff-ffff-ffffffffffff",
        "c0p110t0-aaaa-bbbb-cccc-123456789abc"  # Default GUID
    ]


@pytest.fixture
def invalid_guids():
    """
    Fixture providing invalid GUID formats

    Returns a list of invalid GUID strings for testing
    """
    return [
        "12345678-1234-1234-1234",  # Too short
        "12345678-1234-1234-1234-123456789abcdef",  # Too long
        "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # Invalid characters
        "12345678_1234_1234_1234_123456789abc",  # Wrong delimiter
        "not-a-guid-at-all",
        "",
        None
    ]


# Pytest hooks for custom behavior

def pytest_configure(config):
    """
    Pytest configuration hook

    Adds custom markers and configuration
    """
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual functions"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for components"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests for complete workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "azure: Tests requiring Azure credentials"
    )


def pytest_collection_modifyitems(config, items):
    """
    Pytest collection hook

    Automatically marks tests based on their location
    """
    for item in items:
        # Auto-mark tests based on directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
