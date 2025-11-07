"""
Local LLM Client - Offline/Edge Mode
Provides OpenAI-compatible API using local LLM models
Supports Ollama, llama.cpp, and other local inference engines
No internet or cloud dependencies required
"""
import json
import logging
import requests
from typing import List, Dict, Any, Optional, Union
import os

logger = logging.getLogger(__name__)


class LocalLLMClient:
    """
    Local LLM client for offline/edge deployment.
    Uses Ollama or llama.cpp to run models locally.
    Maintains OpenAI-compatible API for seamless integration.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        backend: str = "ollama"
    ):
        """
        Initialize local LLM client.

        Args:
            model_name: Local model name (e.g., "llama2", "mistral", "phi")
            endpoint: Local inference endpoint URL
            backend: Backend type ("ollama", "llamacpp", "transformers")
        """
        self.backend = backend
        self.model_name = model_name or os.environ.get('LOCAL_LLM_MODEL', 'llama2')

        # Set default endpoints based on backend
        if endpoint:
            self.endpoint = endpoint
        elif backend == "ollama":
            self.endpoint = os.environ.get('OLLAMA_ENDPOINT', 'http://localhost:11434')
        elif backend == "llamacpp":
            self.endpoint = os.environ.get('LLAMACPP_ENDPOINT', 'http://localhost:8080')
        else:
            self.endpoint = 'http://localhost:8080'

        logger.info(f"🤖 Local LLM initialized: {self.backend} @ {self.endpoint}")
        logger.info(f"📦 Model: {self.model_name}")

        # Test connection
        if not self._test_connection():
            logger.warning(f"⚠️  Cannot connect to {self.backend} at {self.endpoint}")
            logger.warning(f"⚠️  Please ensure {self.backend} is running")

    def _test_connection(self) -> bool:
        """Test connection to local LLM backend."""
        try:
            if self.backend == "ollama":
                response = requests.get(f"{self.endpoint}/api/tags", timeout=2)
                return response.status_code == 200
            elif self.backend == "llamacpp":
                response = requests.get(f"{self.endpoint}/health", timeout=2)
                return response.status_code == 200
            return False
        except Exception as e:
            logger.debug(f"Connection test failed: {e}")
            return False

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completion using local LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            functions: Optional list of function definitions for agent calling
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate

        Returns:
            OpenAI-compatible response dict
        """
        try:
            if self.backend == "ollama":
                return self._ollama_chat_completion(
                    messages, functions, temperature, max_tokens, **kwargs
                )
            elif self.backend == "llamacpp":
                return self._llamacpp_chat_completion(
                    messages, functions, temperature, max_tokens, **kwargs
                )
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")
        except Exception as e:
            logger.error(f"❌ Error in chat completion: {e}")
            # Return error response in OpenAI format
            return {
                "id": "error",
                "object": "chat.completion",
                "created": 0,
                "model": self.model_name,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Error: Local LLM unavailable - {str(e)}"
                    },
                    "finish_reason": "error"
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

    def _ollama_chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Ollama-specific chat completion implementation."""

        # Prepare request payload
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        # Handle function calling if provided
        if functions:
            # Add function definitions to system message
            function_instructions = self._format_functions_for_prompt(functions)

            # Find system message or create one
            system_msg_idx = None
            for idx, msg in enumerate(messages):
                if msg.get("role") == "system":
                    system_msg_idx = idx
                    break

            if system_msg_idx is not None:
                # Append to existing system message
                messages[system_msg_idx]["content"] += "\n\n" + function_instructions
            else:
                # Insert new system message at the beginning
                messages.insert(0, {
                    "role": "system",
                    "content": function_instructions
                })

        try:
            response = requests.post(
                f"{self.endpoint}/api/chat",
                json=payload,
                timeout=120  # Generous timeout for edge devices
            )
            response.raise_for_status()

            ollama_response = response.json()

            # Convert Ollama response to OpenAI format
            assistant_message = ollama_response.get("message", {})
            content = assistant_message.get("content", "")

            # Check if response contains function call
            function_call = None
            if functions and self._is_function_call(content):
                function_call = self._parse_function_call(content, functions)

            openai_response = {
                "id": f"ollama-{ollama_response.get('created_at', '0')}",
                "object": "chat.completion",
                "created": 0,
                "model": self.model_name,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content if not function_call else None,
                        "function_call": function_call
                    },
                    "finish_reason": "stop" if not function_call else "function_call"
                }],
                "usage": {
                    "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                    "completion_tokens": ollama_response.get("eval_count", 0),
                    "total_tokens": (
                        ollama_response.get("prompt_eval_count", 0) +
                        ollama_response.get("eval_count", 0)
                    )
                }
            }

            logger.debug(f"✓ Ollama completion: {len(content)} chars")
            return openai_response

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ollama request failed: {e}")
            raise

    def _llamacpp_chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """llama.cpp server-specific chat completion implementation."""

        # Convert messages to prompt format
        prompt = self._messages_to_prompt(messages)

        # Add function calling instructions if needed
        if functions:
            function_instructions = self._format_functions_for_prompt(functions)
            prompt = function_instructions + "\n\n" + prompt

        payload = {
            "prompt": prompt,
            "temperature": temperature,
            "n_predict": max_tokens or 512,
            "stop": ["User:", "Assistant:", "\n\n\n"]
        }

        try:
            response = requests.post(
                f"{self.endpoint}/completion",
                json=payload,
                timeout=120
            )
            response.raise_for_status()

            cpp_response = response.json()
            content = cpp_response.get("content", "").strip()

            # Check for function call
            function_call = None
            if functions and self._is_function_call(content):
                function_call = self._parse_function_call(content, functions)

            openai_response = {
                "id": f"llamacpp-{cpp_response.get('timings', {}).get('start', 0)}",
                "object": "chat.completion",
                "created": 0,
                "model": self.model_name,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content if not function_call else None,
                        "function_call": function_call
                    },
                    "finish_reason": "stop" if not function_call else "function_call"
                }],
                "usage": {
                    "prompt_tokens": cpp_response.get("tokens_evaluated", 0),
                    "completion_tokens": cpp_response.get("tokens_predicted", 0),
                    "total_tokens": (
                        cpp_response.get("tokens_evaluated", 0) +
                        cpp_response.get("tokens_predicted", 0)
                    )
                }
            }

            logger.debug(f"✓ llama.cpp completion: {len(content)} chars")
            return openai_response

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ llama.cpp request failed: {e}")
            raise

    def _format_functions_for_prompt(self, functions: List[Dict]) -> str:
        """
        Format function definitions for inclusion in prompt.
        Teaches the model how to call functions.
        """
        instructions = """FUNCTION CALLING INSTRUCTIONS:
You have access to the following functions. To call a function, respond ONLY with a JSON object in this exact format:

{
  "function": "function_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}

Available functions:
"""
        for func in functions:
            instructions += f"\n{func['name']}: {func.get('description', '')}\n"
            params = func.get('parameters', {}).get('properties', {})
            if params:
                instructions += "Parameters:\n"
                for param_name, param_info in params.items():
                    param_desc = param_info.get('description', '')
                    param_type = param_info.get('type', 'string')
                    instructions += f"  - {param_name} ({param_type}): {param_desc}\n"

        instructions += "\nOnly call functions when explicitly needed. Otherwise, respond normally.\n"
        return instructions

    def _is_function_call(self, content: str) -> bool:
        """Check if response content is a function call."""
        content = content.strip()
        # Check if content looks like JSON with function/arguments
        if content.startswith("{") and content.endswith("}"):
            try:
                data = json.loads(content)
                return "function" in data and "arguments" in data
            except json.JSONDecodeError:
                return False
        return False

    def _parse_function_call(self, content: str, functions: List[Dict]) -> Optional[Dict]:
        """Parse function call from model response."""
        try:
            data = json.loads(content.strip())
            function_name = data.get("function")
            arguments = data.get("arguments", {})

            # Validate function exists
            valid_functions = [f["name"] for f in functions]
            if function_name not in valid_functions:
                logger.warning(f"⚠️  Invalid function call: {function_name}")
                return None

            return {
                "name": function_name,
                "arguments": json.dumps(arguments)
            }
        except Exception as e:
            logger.error(f"❌ Error parsing function call: {e}")
            return None

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI message format to plain text prompt."""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
            elif role == "function":
                function_name = msg.get("name", "unknown")
                prompt_parts.append(f"Function {function_name} returned: {content}")

        prompt_parts.append("Assistant:")
        return "\n\n".join(prompt_parts)

    def list_models(self) -> List[str]:
        """
        List available local models.

        Returns:
            List of model names
        """
        try:
            if self.backend == "ollama":
                response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
                response.raise_for_status()
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                logger.info(f"📦 Available Ollama models: {', '.join(models)}")
                return models
            elif self.backend == "llamacpp":
                # llama.cpp server doesn't have a list endpoint
                # Return currently loaded model
                return [self.model_name]
            return []
        except Exception as e:
            logger.error(f"❌ Error listing models: {e}")
            return []


class LocalLLMClientFactory:
    """Factory for creating local LLM clients based on configuration."""

    @staticmethod
    def create_from_env() -> LocalLLMClient:
        """
        Create LocalLLMClient from environment variables.

        Environment variables:
            LOCAL_LLM_BACKEND: Backend type (ollama, llamacpp)
            LOCAL_LLM_MODEL: Model name
            LOCAL_LLM_ENDPOINT: Custom endpoint URL
            OLLAMA_ENDPOINT: Ollama-specific endpoint
            LLAMACPP_ENDPOINT: llama.cpp-specific endpoint

        Returns:
            Configured LocalLLMClient instance
        """
        backend = os.environ.get('LOCAL_LLM_BACKEND', 'ollama')
        model_name = os.environ.get('LOCAL_LLM_MODEL', 'llama2')
        endpoint = os.environ.get('LOCAL_LLM_ENDPOINT')

        logger.info(f"🏭 Creating LLM client: backend={backend}, model={model_name}")

        return LocalLLMClient(
            model_name=model_name,
            endpoint=endpoint,
            backend=backend
        )
