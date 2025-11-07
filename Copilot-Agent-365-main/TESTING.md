# Testing Infrastructure for AI Ambassador Platform

This document provides comprehensive guidance on testing the AI Ambassador Platform.

## Overview

The testing infrastructure includes:
- **Unit Tests**: Test individual functions and methods in isolation
- **Integration Tests**: Test component interactions and data flow
- **End-to-End Tests**: Test complete user workflows and scenarios
- **CI/CD Integration**: Automated testing via GitHub Actions

## Quick Start

### Install Test Dependencies

```bash
cd Copilot-Agent-365-main
pip install -r requirements.txt
```

This installs all required dependencies including:
- pytest (test framework)
- pytest-cov (coverage reporting)
- pytest-mock (mocking utilities)
- pytest-asyncio (async test support)

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=. --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest tests/unit/ -m unit

# Run only integration tests
pytest tests/integration/ -m integration

# Run only E2E tests
pytest tests/e2e/ -m e2e
```

## Test Structure

```
Copilot-Agent-365-main/
├── tests/
│   ├── __init__.py
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── test_utility_functions.py
│   │   ├── test_agent_loading.py
│   │   └── test_memory_and_guid.py
│   ├── integration/             # Integration tests
│   │   ├── __init__.py
│   │   └── test_request_flow.py
│   ├── e2e/                     # End-to-end tests
│   │   ├── __init__.py
│   │   └── test_conversation_flows.py
│   └── fixtures/                # Test data fixtures
├── conftest.py                  # Pytest configuration and shared fixtures
├── pytest.ini                   # Pytest settings
└── .coveragerc                  # Coverage configuration
```

## Test Coverage

### Current Coverage

The test suite aims for **>80% code coverage** on core modules:

- **Utility Functions**: `ensure_string_content()`, `ensure_string_function_args()`, `build_cors_response()`
- **Agent Loading**: Dynamic agent discovery and loading from local/Azure storage
- **Memory Management**: Context initialization, GUID handling, memory read/write
- **Request Flow**: Complete API request processing pipeline
- **Conversation Handling**: Multi-turn conversations, context maintenance
- **Demo System**: Demo triggering, progression, and completion

### Generate Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View report (opens in browser)
open htmlcov/index.html

# Generate terminal report
pytest --cov=. --cov-report=term-missing
```

## Unit Tests

Unit tests focus on individual functions and methods in isolation.

### Test Categories

#### 1. Utility Functions (`test_utility_functions.py`)

Tests for core utility functions:
- String content sanitization
- Function argument conversion
- CORS header generation

**Example:**
```python
def test_none_message():
    """Test that None message returns default dict with empty content"""
    result = ensure_string_content(None)
    assert result == {"role": "user", "content": ""}
```

#### 2. Agent Loading (`test_agent_loading.py`)

Tests for agent discovery and loading:
- Loading agents from local folder
- Loading agents from Azure File Storage
- Agent metadata validation
- Error handling for failed imports

**Example:**
```python
@patch('function_app.AzureFileStorageManager')
def test_load_agents_from_local_folder(mock_storage):
    """Test loading agents from local folder"""
    result = load_agents_from_folder()
    assert isinstance(result, dict)
```

#### 3. Memory and GUID Handling (`test_memory_and_guid.py`)

Tests for memory context and user identification:
- GUID extraction from user input
- Memory context initialization
- User context switching
- Demo trigger detection

**Example:**
```python
def test_extract_valid_guid():
    """Test extracting valid GUID from text"""
    valid_guid = "12345678-1234-1234-1234-123456789abc"
    result = assistant.extract_user_guid(valid_guid)
    assert result == valid_guid
```

## Integration Tests

Integration tests verify component interactions and data flow.

### Test Categories

#### 1. Request Flow (`test_request_flow.py`)

Tests for complete request processing:
- Simple conversations without agent calls
- Conversations with agent execution
- Multi-turn conversations
- Error handling and recovery
- Memory operations
- User context switching

**Example:**
```python
def test_conversation_with_agent_call():
    """Test conversation that triggers agent execution"""
    # Setup mock OpenAI response with function call
    # Verify agent is executed
    # Check final response
    assert "TestAgent" in logs
```

## End-to-End Tests

E2E tests validate complete user workflows and scenarios.

### Test Categories

#### 1. Conversation Flows (`test_conversation_flows.py`)

Tests for real-world usage patterns:
- Complete conversation scenarios
- Multi-turn context maintenance
- Demo activation and progression
- New user session initialization
- Returning user sessions
- Anonymous user handling

**Example:**
```python
def test_greeting_and_question_flow(mock_assistant):
    """Test basic greeting followed by question"""
    # Turn 1: Greeting
    formatted1, voice1, logs1 = mock_assistant.get_response("Hello", [])

    # Turn 2: Question with history
    conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": formatted1}
    ]
    formatted2, voice2, logs2 = mock_assistant.get_response("What can you do?", conversation_history)
```

## Shared Fixtures

The `conftest.py` file provides shared fixtures available to all tests:

### Available Fixtures

- `mock_azure_storage`: Mock Azure File Storage Manager
- `mock_openai`: Mock Azure OpenAI client
- `mock_environment`: Mock environment variables
- `sample_conversation_history`: Sample conversation data
- `sample_agent_metadata`: Sample agent configuration
- `sample_demo_data`: Sample demo configuration
- `sample_ambassador_config`: Sample ambassador JSON
- `sample_memory_data`: Sample memory entries
- `valid_guids`: List of valid test GUIDs
- `invalid_guids`: List of invalid GUID formats

### Using Fixtures

```python
def test_with_fixtures(mock_azure_storage, valid_guids):
    """Test using shared fixtures"""
    test_guid = valid_guids[0]
    mock_azure_storage.set_memory_context(test_guid)
    # Test logic here
```

## Writing New Tests

### Unit Test Template

```python
"""
Unit tests for [module/function name]

Tests cover:
- [Test category 1]
- [Test category 2]
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from [module] import [function_to_test]


class Test[FunctionName]:
    """Test cases for [function name]"""

    def test_[scenario](self):
        """Test [specific scenario]"""
        # Arrange
        input_data = "test input"

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result == expected_output
```

### Integration Test Template

```python
"""
Integration tests for [component/flow name]

Tests cover:
- [Integration scenario 1]
- [Integration scenario 2]
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class Test[ComponentName]:
    """Test cases for [component] integration"""

    @patch('[external_dependency]')
    def test_[integration_scenario](self, mock_dependency):
        """Test [integration scenario]"""
        # Setup mocks
        mock_dependency.return_value = mock_response

        # Execute integration
        result = component.process()

        # Verify interactions
        assert mock_dependency.called
        assert result == expected
```

## Mocking Best Practices

### Mock Azure Services

Always mock Azure services to avoid requiring credentials:

```python
@patch('function_app.AzureOpenAI')
@patch('function_app.AzureFileStorageManager')
def test_with_azure_mocks(mock_storage, mock_openai):
    """Test with mocked Azure services"""
    mock_storage_instance = MagicMock()
    mock_storage.return_value = mock_storage_instance
    # Test logic
```

### Mock OpenAI Responses

Create mock responses that match the OpenAI API structure:

```python
class MockOpenAIResponse:
    def __init__(self, content=None, function_call=None):
        self.choices = [MagicMock()]
        self.choices[0].message = MagicMock()
        self.choices[0].message.content = content
        self.choices[0].message.function_call = function_call

# Use in tests
mock_response = MockOpenAIResponse(content="Test response|||VOICE|||Voice response")
assistant.client.chat.completions.create.return_value = mock_response
```

## CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/test.yml` file defines automated testing:

**Jobs:**
1. **test**: Runs all tests with coverage reporting
2. **lint**: Code quality checks (flake8, black, isort)
3. **security**: Security scanning (safety, bandit)
4. **test-summary**: Aggregates results and reports status

**Triggers:**
- Push to `main`, `develop`, or `feature/*` branches
- Pull requests to `main` or `develop`
- Manual workflow dispatch

### Running Tests Locally Before Push

```bash
# Run the same tests that CI will run
pytest tests/unit/ -v -m unit
pytest tests/integration/ -v -m integration
pytest tests/e2e/ -v -m e2e

# Run code quality checks
flake8 . --count --select=E9,F63,F7,F82
black --check .
isort --check-only .

# Run security scan
safety check --file requirements.txt
bandit -r .
```

## Test Markers

Tests are automatically marked based on their directory:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests

Additional markers:
- `@pytest.mark.slow`: Tests that take >5 seconds
- `@pytest.mark.azure`: Tests requiring Azure credentials (skipped in CI)

### Running Tests by Marker

```bash
# Run only unit tests
pytest -m unit

# Run all except slow tests
pytest -m "not slow"

# Run unit and integration tests
pytest -m "unit or integration"
```

## Coverage Requirements

**Minimum Coverage Thresholds:**
- Overall: 80%
- Core modules (function_app.py): 85%
- Agent implementations: 70%
- Utility modules: 90%

**Coverage is enforced by:**
- pytest.ini configuration (`fail_under = 80`)
- GitHub Actions workflow (fails if below threshold)
- Pull request coverage comments

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:** `ModuleNotFoundError` when running tests

**Solution:**
```bash
# Ensure you're in the correct directory
cd Copilot-Agent-365-main

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2. Mock Issues

**Problem:** Tests fail due to unmocked Azure services

**Solution:** Always patch Azure dependencies:
```python
@patch('function_app.AzureOpenAI')
@patch('function_app.AzureFileStorageManager')
def test_function(mock_storage, mock_openai):
    # Test logic
```

#### 3. Coverage Not Calculating

**Problem:** Coverage report shows 0% or missing files

**Solution:**
```bash
# Run with explicit coverage configuration
pytest --cov=. --cov-config=.coveragerc
```

#### 4. Fixture Not Found

**Problem:** `fixture 'mock_assistant' not found`

**Solution:** Ensure `conftest.py` is in the correct location and contains the fixture.

## Performance Considerations

### Test Execution Time

**Target Times:**
- Unit tests: <1 second per test
- Integration tests: <5 seconds per test
- E2E tests: <10 seconds per test
- Full suite: <30 seconds

### Optimization Tips

1. **Use mocks instead of real services**
2. **Minimize file I/O operations**
3. **Share expensive fixtures across tests**
4. **Run tests in parallel** (requires pytest-xdist):
   ```bash
   pytest -n auto
   ```

## Continuous Improvement

### Adding New Tests

When adding new functionality:
1. Write unit tests for individual functions
2. Add integration tests for component interactions
3. Create E2E tests for user-facing workflows
4. Update this documentation with new test categories

### Test Maintenance

- Review and update tests when functionality changes
- Remove obsolete tests
- Refactor duplicate test code into fixtures
- Keep test execution time under target thresholds

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Azure Functions Python Testing](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)

## Contact

For questions or issues with the testing infrastructure:
- Open an issue on GitHub
- Review existing tests for examples
- Check CI/CD logs for detailed error messages
