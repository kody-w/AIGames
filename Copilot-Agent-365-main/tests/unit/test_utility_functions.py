"""
Unit tests for utility functions in function_app.py

Tests cover:
- ensure_string_content()
- ensure_string_function_args()
- build_cors_response()
"""

import pytest
import sys
import os

# Add the parent directory to the path so we can import function_app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from function_app import ensure_string_content, ensure_string_function_args, build_cors_response


class TestEnsureStringContent:
    """Test cases for ensure_string_content() function"""

    def test_none_message(self):
        """Test that None message returns default dict with empty content"""
        result = ensure_string_content(None)
        assert result == {"role": "user", "content": ""}

    def test_valid_message_with_content(self):
        """Test valid message with content is preserved"""
        message = {"role": "assistant", "content": "Hello world"}
        result = ensure_string_content(message)
        assert result == {"role": "assistant", "content": "Hello world"}

    def test_message_with_none_content(self):
        """Test message with None content gets converted to empty string"""
        message = {"role": "user", "content": None}
        result = ensure_string_content(message)
        assert result == {"role": "user", "content": ""}

    def test_message_without_content_key(self):
        """Test message missing content key gets empty string"""
        message = {"role": "system"}
        result = ensure_string_content(message)
        assert result == {"role": "system", "content": ""}

    def test_message_without_role(self):
        """Test message without role gets default user role"""
        message = {"content": "Test content"}
        result = ensure_string_content(message)
        assert result == {"role": "user", "content": "Test content"}

    def test_non_dict_message(self):
        """Test non-dict message gets converted properly"""
        result = ensure_string_content("Just a string")
        assert result == {"role": "user", "content": "Just a string"}

    def test_integer_content(self):
        """Test integer content gets converted to string"""
        message = {"role": "user", "content": 42}
        result = ensure_string_content(message)
        assert result == {"role": "user", "content": "42"}

    def test_list_content(self):
        """Test list content gets converted to string"""
        message = {"role": "user", "content": [1, 2, 3]}
        result = ensure_string_content(message)
        assert result == {"role": "user", "content": "[1, 2, 3]"}

    def test_original_message_not_modified(self):
        """Test that original message dict is not modified"""
        original = {"role": "user", "content": None}
        result = ensure_string_content(original)
        assert original["content"] is None  # Original should remain unchanged
        assert result["content"] == ""


class MockFunctionCall:
    """Mock class for OpenAI function call objects"""
    def __init__(self, arguments):
        self.arguments = arguments


class TestEnsureStringFunctionArgs:
    """Test cases for ensure_string_function_args() function"""

    def test_none_function_call(self):
        """Test None function call returns None"""
        result = ensure_string_function_args(None)
        assert result is None

    def test_function_call_without_arguments_attribute(self):
        """Test function call without arguments attribute returns None"""
        mock_call = object()  # Plain object with no attributes
        result = ensure_string_function_args(mock_call)
        assert result is None

    def test_function_call_with_none_arguments(self):
        """Test function call with None arguments returns None"""
        mock_call = MockFunctionCall(None)
        result = ensure_string_function_args(mock_call)
        assert result is None

    def test_function_call_with_dict_arguments(self):
        """Test function call with dict arguments gets JSON stringified"""
        args = {"param1": "value1", "param2": 42}
        mock_call = MockFunctionCall(args)
        result = ensure_string_function_args(mock_call)
        assert result == '{"param1": "value1", "param2": 42}'

    def test_function_call_with_list_arguments(self):
        """Test function call with list arguments gets JSON stringified"""
        args = [1, 2, 3, "test"]
        mock_call = MockFunctionCall(args)
        result = ensure_string_function_args(mock_call)
        assert result == '[1, 2, 3, "test"]'

    def test_function_call_with_string_arguments(self):
        """Test function call with string arguments returns string"""
        mock_call = MockFunctionCall("already a string")
        result = ensure_string_function_args(mock_call)
        assert result == "already a string"

    def test_function_call_with_integer_arguments(self):
        """Test function call with integer arguments converts to string"""
        mock_call = MockFunctionCall(123)
        result = ensure_string_function_args(mock_call)
        assert result == "123"


class TestBuildCorsResponse:
    """Test cases for build_cors_response() function"""

    def test_with_valid_origin(self):
        """Test CORS headers with valid origin"""
        origin = "https://example.com"
        result = build_cors_response(origin)

        assert result["Access-Control-Allow-Origin"] == "https://example.com"
        assert result["Access-Control-Allow-Methods"] == "*"
        assert result["Access-Control-Allow-Headers"] == "*"
        assert result["Access-Control-Allow-Credentials"] == "true"
        assert result["Access-Control-Max-Age"] == "86400"

    def test_with_none_origin(self):
        """Test CORS headers with None origin defaults to *"""
        result = build_cors_response(None)
        assert result["Access-Control-Allow-Origin"] == "*"

    def test_with_empty_string_origin(self):
        """Test CORS headers with empty string origin"""
        result = build_cors_response("")
        assert result["Access-Control-Allow-Origin"] == "*"

    def test_with_localhost_origin(self):
        """Test CORS headers with localhost origin"""
        origin = "http://localhost:3000"
        result = build_cors_response(origin)
        assert result["Access-Control-Allow-Origin"] == "http://localhost:3000"

    def test_headers_structure(self):
        """Test that all required CORS headers are present"""
        result = build_cors_response("https://test.com")

        required_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
            "Access-Control-Allow-Credentials",
            "Access-Control-Max-Age"
        ]

        for header in required_headers:
            assert header in result

    def test_credentials_is_string(self):
        """Test that credentials value is string 'true'"""
        result = build_cors_response("https://test.com")
        assert result["Access-Control-Allow-Credentials"] == "true"
        assert isinstance(result["Access-Control-Allow-Credentials"], str)
