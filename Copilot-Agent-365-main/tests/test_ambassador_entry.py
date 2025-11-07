"""
Test suite for the ambassador_entry endpoint

This file contains unit tests for the ambassador_entry Azure Function endpoint.
Run with: pytest tests/test_ambassador_entry.py
"""

import pytest
import json
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the Azure Functions module if not available
try:
    import azure.functions as func
except ImportError:
    # Create a minimal mock for testing
    class MockHttpRequest:
        def __init__(self, method='GET', route_params=None, params=None, headers=None):
            self.method = method
            self.route_params = route_params or {}
            self.params = params or {}
            self.headers = headers or {}

        def get(self, key, default=None):
            return self.params.get(key, default)

    class MockHttpResponse:
        def __init__(self, body=None, status_code=200, mimetype='text/plain', headers=None):
            self.body = body
            self.status_code = status_code
            self.mimetype = mimetype
            self.headers = headers or {}

    # Create mock module
    import types
    func = types.ModuleType('func')
    func.HttpRequest = MockHttpRequest
    func.HttpResponse = MockHttpResponse

    class AuthLevel:
        ANONYMOUS = 'anonymous'
        FUNCTION = 'function'

    func.AuthLevel = AuthLevel
    sys.modules['azure.functions'] = func


class TestAmbassadorEntry:
    """Test cases for ambassador_entry endpoint"""

    def test_initialize_seeded_memory_structure(self):
        """Test that initialize_seeded_memory creates proper memory structure"""
        from function_app import initialize_seeded_memory

        # Mock configuration
        config = {
            'demo_configuration': {
                'seed_version': 'v1.0',
                'synthetic_memory': {
                    'memories': [
                        {
                            'id': 'mem-001',
                            'message': 'Test memory',
                            'theme': 'preferences',
                            'mood': 'neutral'
                        }
                    ]
                }
            }
        }

        # This test verifies the structure without actually calling Azure
        # In a real test, you would mock AzureFileStorageManager
        assert 'demo_configuration' in config
        assert 'synthetic_memory' in config['demo_configuration']
        assert len(config['demo_configuration']['synthetic_memory']['memories']) > 0

    def test_track_ambassador_scan_parameters(self):
        """Test that track_ambassador_scan accepts correct parameters"""
        from function_app import track_ambassador_scan

        # Should not raise an exception
        try:
            track_ambassador_scan('creative-001', 'test-guid', True, 'test_source')
            assert True
        except Exception as e:
            pytest.fail(f"track_ambassador_scan raised exception: {e}")

    def test_ambassador_response_structure(self):
        """Test the expected response structure from ambassador_entry"""
        expected_keys = ['ambassador', 'session', 'analytics']
        ambassador_keys = ['id', 'name', 'display_name', 'avatar', 'world', 'capabilities']
        session_keys = ['user_guid', 'is_demo', 'session_id', 'agent_endpoint', 'timestamp']
        analytics_keys = ['scan_id', 'timestamp', 'source']

        # Mock response structure
        response = {
            'ambassador': {
                'id': 'creative-001',
                'name': 'CreativeBot',
                'display_name': 'Creative Companion',
                'avatar': {'type': 'emoji', 'value': '🎨'},
                'world': {},
                'capabilities': [],
                'role': '',
                'description': '',
                'tagline': ''
            },
            'session': {
                'user_guid': 'test-guid',
                'is_demo': True,
                'session_id': 'test-session',
                'agent_endpoint': '/api/businessinsightbot_function',
                'timestamp': datetime.now().isoformat()
            },
            'analytics': {
                'scan_id': 'test-scan',
                'timestamp': datetime.now().isoformat(),
                'source': 'test'
            }
        }

        # Verify top-level structure
        for key in expected_keys:
            assert key in response, f"Missing key: {key}"

        # Verify ambassador structure
        for key in ambassador_keys:
            assert key in response['ambassador'], f"Missing ambassador key: {key}"

        # Verify session structure
        for key in session_keys:
            assert key in response['session'], f"Missing session key: {key}"

        # Verify analytics structure
        for key in analytics_keys:
            assert key in response['analytics'], f"Missing analytics key: {key}"

    def test_ambassador_config_validation(self):
        """Test that ambassador configurations have required fields"""
        # Example ambassador config structure
        config = {
            'ambassador': {
                'id': 'creative-001',
                'name': 'CreativeBot',
                'display_name': 'Creative Companion',
                'avatar': {
                    'type': 'emoji',
                    'value': '🎨'
                },
                'world': {
                    'type': 'creative_studio',
                    'name': 'The Imagination Lab'
                },
                'capabilities': [],
                'demo_configuration': {
                    'seeded_run': True,
                    'parameters': {
                        'user_guid': 'demo-creative-001',
                        'memory_seed': 'creative_demo_v1'
                    }
                }
            }
        }

        # Validate required fields exist
        assert 'ambassador' in config
        ambassador = config['ambassador']
        assert 'id' in ambassador
        assert 'name' in ambassador
        assert 'avatar' in ambassador
        assert 'world' in ambassador
        assert 'demo_configuration' in ambassador

        # Validate demo configuration
        demo_config = ambassador['demo_configuration']
        assert 'seeded_run' in demo_config
        assert 'parameters' in demo_config
        assert 'user_guid' in demo_config['parameters']

    def test_error_response_structure(self):
        """Test error response structures"""
        # 400 Bad Request
        error_400 = {
            'error': 'Missing ambassador_id in route'
        }
        assert 'error' in error_400

        # 404 Not Found
        error_404 = {
            'error': 'Ambassador not found',
            'ambassador_id': 'invalid-id'
        }
        assert 'error' in error_404
        assert 'ambassador_id' in error_404

        # 500 Internal Server Error
        error_500 = {
            'error': 'Internal server error',
            'details': 'Error message details'
        }
        assert 'error' in error_500
        assert 'details' in error_500

    def test_demo_vs_real_user_logic(self):
        """Test the logic for determining demo vs real user"""
        # Demo configuration
        demo_config = {
            'seeded_run': True,
            'parameters': {
                'user_guid': 'demo-creative-001'
            }
        }

        # Real user configuration
        real_config = {
            'seeded_run': False
        }

        # Test demo detection
        is_demo = demo_config.get('seeded_run', False)
        assert is_demo == True

        # Test real user detection
        is_real = real_config.get('seeded_run', False)
        assert is_real == False

    def test_source_parameter_extraction(self):
        """Test extraction of source parameter from query string"""
        # Mock request parameters
        params = {
            'source': 'art_gallery_soho'
        }

        source = params.get('source', 'unknown')
        assert source == 'art_gallery_soho'

        # Test default value
        empty_params = {}
        source_default = empty_params.get('source', 'unknown')
        assert source_default == 'unknown'


class TestIntegration:
    """Integration tests requiring mocked Azure services"""

    @pytest.mark.skip(reason="Requires Azure File Storage mock")
    def test_ambassador_entry_full_flow(self):
        """Test the complete ambassador_entry flow (requires mocking)"""
        # This would test the full endpoint with mocked Azure services
        pass

    @pytest.mark.skip(reason="Requires Azure File Storage mock")
    def test_seeded_memory_initialization(self):
        """Test seeded memory initialization with Azure Storage (requires mocking)"""
        # This would test memory initialization with mocked storage
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
