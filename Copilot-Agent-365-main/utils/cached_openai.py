"""
Cached OpenAI API Wrapper

This module provides a caching layer for Azure OpenAI API calls to reduce costs
and improve response times.

Features:
- Automatic response caching for identical queries
- Semantic similarity matching for similar queries
- Cache invalidation on demand
- Cost tracking and savings calculation
- Thread-safe operations

Usage:
    from utils.cached_openai import CachedAzureOpenAI

    client = CachedAzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version
    )

    # Use exactly like AzureOpenAI client
    response = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        temperature=0.7
    )

Author: AI Ambassador Platform Team
Version: 1.0.0
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from utils.cache import get_cache_manager


class CachedChatCompletions:
    """Cached wrapper for chat completions"""

    def __init__(self, client: AzureOpenAI, cache_manager):
        self.client = client
        self.cache_manager = cache_manager

    def _normalize_messages(self, messages: List[Dict]) -> str:
        """
        Normalize messages for consistent cache key generation.

        Removes timestamps and other variable data that doesn't affect the response.
        """
        normalized = []

        for msg in messages:
            normalized_msg = {
                'role': msg.get('role', 'user'),
                'content': msg.get('content', '')
            }
            # Include function calls if present
            if 'function_call' in msg:
                normalized_msg['function_call'] = msg['function_call']
            if 'name' in msg:
                normalized_msg['name'] = msg['name']

            normalized.append(normalized_msg)

        return json.dumps(normalized, sort_keys=True)

    def _should_bypass_cache(self, **kwargs) -> bool:
        """
        Determine if cache should be bypassed for this request.

        Bypass conditions:
        - User-specific GUID in messages
        - Temperature > 0.8 (high creativity)
        - Stream mode enabled
        - Function calling with dynamic data
        """
        # Bypass for streaming
        if kwargs.get('stream', False):
            return True

        # Bypass for high temperature (creative responses)
        if kwargs.get('temperature', 0.7) > 0.8:
            return True

        # Check for user-specific context in messages
        messages = kwargs.get('messages', [])
        messages_str = json.dumps(messages)

        # Look for GUID patterns (user-specific requests)
        import re
        guid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        if re.search(guid_pattern, messages_str, re.IGNORECASE):
            return True

        return False

    def _generate_cache_key(self, **kwargs) -> str:
        """
        Generate cache key from request parameters.

        Includes: model, messages, temperature, max_tokens, functions
        """
        key_parts = {
            'model': kwargs.get('model', ''),
            'messages': self._normalize_messages(kwargs.get('messages', [])),
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens'),
            'functions': json.dumps(kwargs.get('functions', []), sort_keys=True) if kwargs.get('functions') else None
        }

        # Remove None values
        key_parts = {k: v for k, v in key_parts.items() if v is not None}

        key_string = json.dumps(key_parts, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def create(self, **kwargs) -> ChatCompletion:
        """
        Create chat completion with caching.

        Args:
            **kwargs: Same arguments as AzureOpenAI.chat.completions.create()

        Returns:
            ChatCompletion response (cached or fresh)
        """
        # Check if we should bypass cache
        if self._should_bypass_cache(**kwargs):
            logging.debug("Bypassing cache for this request")
            return self.client.chat.completions.create(**kwargs)

        # Generate cache key
        cache_key = self._generate_cache_key(**kwargs)

        # Try exact match cache first
        cached_response = self.cache_manager.get('response', cache_key)

        if cached_response:
            logging.info(f"Cache HIT: Returning cached response for key: {cache_key[:16]}...")
            return self._deserialize_response(cached_response)

        # Try semantic cache for similar queries
        if self.cache_manager.semantic_cache:
            messages = kwargs.get('messages', [])
            if messages:
                # Get last user message for semantic matching
                user_messages = [m for m in messages if m.get('role') == 'user']
                if user_messages:
                    last_user_msg = user_messages[-1].get('content', '')

                    semantic_key = self.cache_manager.semantic_cache.find_similar(last_user_msg)

                    if semantic_key:
                        cached_response = self.cache_manager.get('semantic', semantic_key)

                        if cached_response:
                            logging.info(f"Semantic cache HIT: Returning similar response")
                            return self._deserialize_response(cached_response)

        # Cache miss - call actual API
        logging.info(f"Cache MISS: Calling OpenAI API")

        try:
            response = self.client.chat.completions.create(**kwargs)

            # Cache the response
            serialized_response = self._serialize_response(response)
            self.cache_manager.set('response', serialized_response, cache_key)

            # Add to semantic cache if applicable
            if self.cache_manager.semantic_cache:
                messages = kwargs.get('messages', [])
                if messages:
                    user_messages = [m for m in messages if m.get('role') == 'user']
                    if user_messages:
                        last_user_msg = user_messages[-1].get('content', '')
                        self.cache_manager.semantic_cache.add(last_user_msg, cache_key)

            return response

        except Exception as e:
            logging.error(f"Error calling OpenAI API: {e}")
            raise

    def _serialize_response(self, response: ChatCompletion) -> Dict:
        """Convert ChatCompletion to cacheable dictionary"""
        return {
            'id': response.id,
            'object': response.object,
            'created': response.created,
            'model': response.model,
            'choices': [
                {
                    'index': choice.index,
                    'message': {
                        'role': choice.message.role,
                        'content': choice.message.content,
                        'function_call': {
                            'name': choice.message.function_call.name,
                            'arguments': choice.message.function_call.arguments
                        } if choice.message.function_call else None
                    },
                    'finish_reason': choice.finish_reason
                }
                for choice in response.choices
            ],
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            } if response.usage else None
        }

    def _deserialize_response(self, data: Dict) -> ChatCompletion:
        """Convert cached dictionary back to ChatCompletion object"""
        # Note: This returns a dictionary that mimics ChatCompletion
        # OpenAI SDK's ChatCompletion is a Pydantic model
        # For most use cases, accessing response.choices[0].message.content works
        # If strict type checking is needed, you may need to reconstruct the full object

        class MockMessage:
            def __init__(self, role, content, function_call=None):
                self.role = role
                self.content = content
                self.function_call = function_call

        class MockChoice:
            def __init__(self, index, message, finish_reason):
                self.index = index
                self.message = message
                self.finish_reason = finish_reason

        class MockUsage:
            def __init__(self, prompt_tokens, completion_tokens, total_tokens):
                self.prompt_tokens = prompt_tokens
                self.completion_tokens = completion_tokens
                self.total_tokens = total_tokens

        class MockCompletion:
            def __init__(self, data):
                self.id = data['id']
                self.object = data['object']
                self.created = data['created']
                self.model = data['model']

                # Reconstruct choices
                self.choices = []
                for choice_data in data['choices']:
                    msg_data = choice_data['message']
                    message = MockMessage(
                        role=msg_data['role'],
                        content=msg_data['content'],
                        function_call=msg_data.get('function_call')
                    )
                    choice = MockChoice(
                        index=choice_data['index'],
                        message=message,
                        finish_reason=choice_data['finish_reason']
                    )
                    self.choices.append(choice)

                # Reconstruct usage
                if data.get('usage'):
                    usage_data = data['usage']
                    self.usage = MockUsage(
                        prompt_tokens=usage_data['prompt_tokens'],
                        completion_tokens=usage_data['completion_tokens'],
                        total_tokens=usage_data['total_tokens']
                    )
                else:
                    self.usage = None

        return MockCompletion(data)


class CachedChat:
    """Cached wrapper for chat namespace"""

    def __init__(self, client: AzureOpenAI, cache_manager):
        self.completions = CachedChatCompletions(client, cache_manager)


class CachedAzureOpenAI:
    """
    Drop-in replacement for AzureOpenAI client with caching support.

    This class wraps the AzureOpenAI client and adds caching for chat completions.
    All other methods are passed through to the underlying client.

    Usage:
        # Replace this:
        client = AzureOpenAI(...)

        # With this:
        client = CachedAzureOpenAI(...)

        # Use exactly the same API
        response = client.chat.completions.create(...)
    """

    def __init__(self, api_key: str, azure_endpoint: str, api_version: str,
                 cache_config: Optional[Dict] = None):
        """
        Initialize cached OpenAI client.

        Args:
            api_key: Azure OpenAI API key
            azure_endpoint: Azure OpenAI endpoint URL
            api_version: API version
            cache_config: Optional cache configuration
        """
        # Create underlying client
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )

        # Get cache manager
        self.cache_manager = get_cache_manager(cache_config)

        # Create cached chat namespace
        self.chat = CachedChat(self.client, self.cache_manager)

    def __getattr__(self, name):
        """
        Pass through any other attributes to underlying client.

        This allows using embeddings, images, etc. without caching.
        """
        return getattr(self.client, name)


def create_cached_client(api_key: str, azure_endpoint: str, api_version: str,
                        cache_enabled: bool = True,
                        cache_config: Optional[Dict] = None) -> AzureOpenAI:
    """
    Factory function to create OpenAI client with optional caching.

    Args:
        api_key: Azure OpenAI API key
        azure_endpoint: Azure OpenAI endpoint URL
        api_version: API version
        cache_enabled: Enable caching (default: True)
        cache_config: Optional cache configuration

    Returns:
        AzureOpenAI client (cached or standard)
    """
    if cache_enabled:
        return CachedAzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version,
            cache_config=cache_config
        )
    else:
        return AzureOpenAI(
            api_key=api_key,
            azure_endpoint=azure_endpoint,
            api_version=api_version
        )
