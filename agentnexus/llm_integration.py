"""
LLM Integration for AgentNexus using established OSS libraries.

This module provides a simple interface to use LLMs in AgentNexus by
leveraging standard OSS libraries like Instructor, LiteLLM, and LangChain.
"""
from typing import Dict, List, Any, Optional, Union, Type, TypeVar, get_type_hints, Callable
import os
import json
import inspect
from functools import lru_cache
from pydantic import BaseModel, Field, create_model
from loguru import logger

# Import LiteLLM for unified LLM API
try:
    import litellm
    from litellm import completion
    LITELLM_AVAILABLE = True
except ImportError:
    logger.warning("LiteLLM not installed. Run `pip install litellm` for enhanced LLM compatibility.")
    LITELLM_AVAILABLE = False

# Import Instructor for structured outputs
try:
    import instructor
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    logger.warning("Instructor not installed. Run `pip install instructor` for structured outputs.")
    INSTRUCTOR_AVAILABLE = False

# Import LangChain for advanced features (optional)
try:
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not installed. Some advanced features may not be available.")
    LANGCHAIN_AVAILABLE = False

# Re-export models from Pydantic for convenience
T = TypeVar('T', bound=BaseModel)

# =============================================================================
# Core Configuration
# =============================================================================

class LLMConfig(BaseModel):
    """Configuration for LLM client."""
    provider: str = Field(default="openai")
    model: str = Field(default="gpt-3.5-turbo")
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    timeout: float = Field(default=300.0)
    max_retries: int = Field(default=3)
    temperature: float = Field(default=0.7)
    dry_run: bool = Field(default=False)
    additional_options: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"

    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            provider=os.environ.get("LLM_PROVIDER", "openai"),
            model=os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
            api_key=os.environ.get("LLM_API_KEY"),
            api_base=os.environ.get("LLM_BASE_URL"),
            timeout=float(os.environ.get("LLM_TIMEOUT", "300.0")),
            dry_run=os.environ.get("LLM_DRY_RUN", "False").lower() == "true",
        )

# =============================================================================
# LLM Client
# =============================================================================

class LLMClient:
    """
    Universal LLM client that works with multiple providers.

    This client uses LiteLLM to provide a unified interface to various
    LLM providers, with fallback to direct provider APIs when needed.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM client with configuration."""
        self.config = config or LLMConfig.from_env()

        # Configure LiteLLM if available
        if LITELLM_AVAILABLE:
            # Register any custom provider if needed
            if self.config.provider in ["qwen", "deepseek"]:
                # Map DeepSeek/Qwen to LiteLLM's compatible provider
                self._setup_deepseek_qwen()

        # Set up Instructor if available
        if INSTRUCTOR_AVAILABLE:
            self.instructor_client = self._create_instructor_client()

    def _setup_deepseek_qwen(self):
        """Configure LiteLLM for DeepSeek/Qwen support."""
        # Check if we need to register a custom provider
        # For most DeepSeek/Qwen deployments, they're compatible with OpenAI API
        if self.config.api_base:
            # Register the model with LiteLLM
            litellm.add_model({
                "model_name": self.config.model,
                "litellm_provider": "openai",  # Use OpenAI-compatible API
                "api_base": self.config.api_base,
                "api_key": self.config.api_key or "dummy-key"
            })

    def _create_instructor_client(self):
        """Create an Instructor client for structured outputs."""
        if self.config.provider == "openai":
            # Standard OpenAI client
            from openai import OpenAI
            client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
            return instructor.patch(client)
        elif self.config.provider in ["qwen", "deepseek"]:
            # DeepSeek/Qwen using a custom adapter
            return self._create_custom_instructor_client()
        else:
            # Use LiteLLM for other providers
            return instructor.from_litellm(
                model=self.config.model,
                api_key=self.config.api_key,
                api_base=self.config.api_base
            )

    def _create_custom_instructor_client(self):
        """Create a custom Instructor client for DeepSeek/Qwen."""
        try:
            # Use instructor.from_openai with custom base URL
            from openai import OpenAI
            client = OpenAI(
                api_key=self.config.api_key or "dummy-key",
                base_url=self.config.api_base,
                timeout=self.config.timeout
            )
            return instructor.patch(client)
        except Exception as e:
            logger.warning(f"Failed to create custom Instructor client: {e}")
            logger.warning("Falling back to standard implementation.")
            return None

    async def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """Send a completion request to the LLM."""
        # Handle dry run mode
        if self.config.dry_run:
            logger.info(f"[DRY RUN] LLM Completion request:")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"System: {system_message}")
            return f"[DRY RUN] This is a simulated response for: {prompt[:50]}..."

        # Get final parameters, merging config with kwargs
        params = {
            "model": self.config.model,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", None),
            "timeout": self.config.timeout,
        }

        # Add provider-specific options
        if self.config.provider in ["qwen", "deepseek"]:
            params["stop"] = kwargs.get("stop", None)
            params["top_p"] = kwargs.get("top_p", 0.9)

        if LITELLM_AVAILABLE:
            try:
                # Use LiteLLM for completion
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": prompt})

                response = await litellm.acompletion(
                    model=self.config.model,
                    messages=messages,
                    api_key=self.config.api_key,
                    api_base=self.config.api_base,
                    **params
                )

                # Extract content from response
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LiteLLM error: {e}")
                # Fall back to direct provider implementation

        # Direct implementation for DeepSeek/Qwen
        if self.config.provider in ["qwen", "deepseek"]:
            return await self._complete_with_deepseek_qwen(prompt, system_message, **params)

        # Fallback for other providers
        raise ValueError(f"Provider {self.config.provider} not supported without LiteLLM")

    async def _complete_with_deepseek_qwen(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """Direct implementation for DeepSeek/Qwen."""
        import aiohttp

        # Prepare request payload
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens"),
            "stream": False,
            "top_p": kwargs.get("top_p", 0.9),
            "stop": kwargs.get("stop"),
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        # Make request
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.config.api_key or 'dummy-key'}",
                "Content-Type": "application/json"
            }

            try:
                async with session.post(
                    f"{self.config.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"API error ({response.status}): {error_text}")

                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"DeepSeek/Qwen API error: {e}")
                raise

    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Send a chat completion request to the LLM."""
        # Handle dry run mode
        if self.config.dry_run:
            logger.info(f"[DRY RUN] LLM Chat request:")
            logger.info(f"Messages: {messages}")
            return f"[DRY RUN] This is a simulated chat response"

        # Get final parameters
        params = {
            "model": self.config.model,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", None),
            "timeout": self.config.timeout,
        }

        if LITELLM_AVAILABLE:
            try:
                # Use LiteLLM for chat completion
                response = await litellm.acompletion(
                    model=self.config.model,
                    messages=messages,
                    api_key=self.config.api_key,
                    api_base=self.config.api_base,
                    **params
                )

                # Extract content from response
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"LiteLLM error: {e}")
                # Fall back to direct provider implementation

        # Direct implementation for DeepSeek/Qwen
        if self.config.provider in ["qwen", "deepseek"]:
            return await self._chat_with_deepseek_qwen(messages, **params)

        # Fallback for other providers
        raise ValueError(f"Provider {self.config.provider} not supported without LiteLLM")

    async def _chat_with_deepseek_qwen(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Direct implementation for DeepSeek/Qwen chat."""
        import aiohttp

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens"),
            "stream": False,
            "top_p": kwargs.get("top_p", 0.9),
            "stop": kwargs.get("stop"),
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        # Make request
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.config.api_key or 'dummy-key'}",
                "Content-Type": "application/json"
            }

            try:
                async with session.post(
                    f"{self.config.api_base}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.config.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"API error ({response.status}): {error_text}")

                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
            except Exception as e:
                logger.error(f"DeepSeek/Qwen API error: {e}")
                raise

    async def structured_output(
        self,
        prompt: str,
        output_class: Type[T],
        system_message: Optional[str] = None,
        **kwargs
    ) -> T:
        """Get structured output using Instructor."""
        if not INSTRUCTOR_AVAILABLE:
            raise ImportError("Instructor is required for structured_output. Install with `pip install instructor`.")

        # Handle dry run mode
        if self.config.dry_run:
            logger.info(f"[DRY RUN] LLM Structured Output request:")
            logger.info(f"Prompt: {prompt}")
            logger.info(f"Model: {output_class.__name__}")
            # Create a sample instance with default values
            return self._create_sample_instance(output_class)

        if not self.instructor_client:
            raise ValueError("Instructor client not initialized")

        # Prepare system message
        if not system_message:
            system_message = f"Extract information from the user query and return a valid {output_class.__name__} object."

        try:
            # Call Instructor for structured output
            response = await self.instructor_client.chat.completions.create(
                model=self.config.model,
                response_model=output_class,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=kwargs.get("temperature", self.config.temperature),
                max_tokens=kwargs.get("max_tokens", None),
            )
            return response
        except Exception as e:
            logger.error(f"Structured output error: {e}")
            # Fall back to parsing ourselves
            return await self._fallback_structured_output(prompt, output_class, system_message, **kwargs)

    async def _fallback_structured_output(
        self,
        prompt: str,
        output_class: Type[T],
        system_message: Optional[str] = None,
        **kwargs
    ) -> T:
        """Fallback implementation for structured output."""
        # Add instructions to format as JSON
        enhanced_prompt = f"""
        {prompt}

        Format the response as a valid JSON object that matches this schema:
        {json.dumps(output_class.model_json_schema(), indent=2)}

        The response should be ONLY the JSON object, nothing else.
        """

        # Get completion
        response_text = await self.complete(
            prompt=enhanced_prompt,
            system_message=system_message,
            **kwargs
        )

        # Try to extract JSON
        try:
            # First try to parse the whole response
            data = json.loads(response_text)
            return output_class.model_validate(data)
        except json.JSONDecodeError:
            # Try to extract JSON using regex
            import re
            json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1).strip())
                    return output_class.model_validate(data)
                except (json.JSONDecodeError, ValueError):
                    pass

            # Last resort: try to validate with error handling
            try:
                return output_class.model_validate_json(response_text)
            except Exception as e:
                logger.error(f"Failed to parse structured output: {e}")
                # Create an instance with default values and include the error
                instance = self._create_sample_instance(output_class)
                setattr(instance, "error", str(e))
                return instance

    def _create_sample_instance(self, output_class: Type[T]) -> T:
        """Create a sample instance of a Pydantic class for dry run mode."""
        # Get field definitions
        field_values = {}
        for field_name, field in output_class.model_fields.items():
            # Use default if available
            if field.default is not None and field.default is not ...:
                field_values[field_name] = field.default
            # Otherwise use a type-appropriate sample value
            elif field.annotation:
                field_values[field_name] = self._get_sample_value(field.annotation)

        # Create the instance
        return output_class.model_validate(field_values)

    def _get_sample_value(self, annotation: Any) -> Any:
        """Get a sample value for a type annotation."""
        # Handle basic types
        if annotation == str:
            return "[Sample text]"
        elif annotation == int:
            return 42
        elif annotation == float:
            return 3.14
        elif annotation == bool:
            return True
        elif annotation == list:
            return []
        elif annotation == dict:
            return {}
        # Handle optional types
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
            # Check if it's Optional[Type]
            for arg in annotation.__args__:
                if arg is not type(None):
                    return self._get_sample_value(arg)
            return None
        # Handle list types
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is list:
            item_type = annotation.__args__[0]
            return [self._get_sample_value(item_type)]
        # Handle dict types
        elif hasattr(annotation, "__origin__") and annotation.__origin__ is dict:
            key_type, value_type = annotation.__args__
            return {str(self._get_sample_value(key_type)): self._get_sample_value(value_type)}
        # Handle Pydantic models
        elif hasattr(annotation, "model_fields"):
            return self._create_sample_instance(annotation)
        # Default
        return None

# =============================================================================
# Memory System
# =============================================================================

class Memory:
    """Simple memory system for storing conversation history."""

    def __init__(self, user_id: str, max_history: int = 10):
        """Initialize memory for a user."""
        self.user_id = user_id
        self.max_history = max_history
        self.history = []

    def add(self, role: str, content: str):
        """Add a message to memory."""
        self.history.append({"role": role, "content": content})
        # Trim to max history
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_history(self) -> List[Dict[str, str]]:
        """Get the conversation history."""
        return self.history.copy()

    def clear(self):
        """Clear the memory."""
        self.history = []

# Global memory store
_memory_store: Dict[str, Memory] = {}

def get_memory(user_id: str) -> Memory:
    """Get or create memory for a user."""
    if user_id not in _memory_store:
        _memory_store[user_id] = Memory(user_id)
    return _memory_store[user_id]

# =============================================================================
# Convenience Functions
# =============================================================================

@lru_cache
def get_llm_client(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None
) -> LLMClient:
    """Get a cached LLM client with the specified configuration."""
    config = LLMConfig(
        provider=provider or os.environ.get("LLM_PROVIDER", "openai"),
        model=model or os.environ.get("LLM_MODEL", "gpt-3.5-turbo"),
        api_key=api_key or os.environ.get("LLM_API_KEY"),
        api_base=api_base or os.environ.get("LLM_BASE_URL"),
        timeout=float(os.environ.get("LLM_TIMEOUT", "300.0")),
        dry_run=os.environ.get("LLM_DRY_RUN", "False").lower() == "true",
    )
    return LLMClient(config)

async def ask(
    prompt: str,
    system_message: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Simple function to ask the LLM a question.

    Args:
        prompt: The question or prompt for the LLM
        system_message: Optional system message/instruction
        user_id: Optional user ID for maintaining conversation history
        **kwargs: Additional parameters for the LLM

    Returns:
        The LLM's response as a string
    """
    client = get_llm_client()

    if user_id:
        # Get memory for this user
        memory = get_memory(user_id)
        # Add new message to memory
        memory.add("user", prompt)
        # Create messages with history
        messages = memory.get_history()
        # Add system message if provided
        if system_message:
            messages = [{"role": "system", "content": system_message}] + messages
        # Get response
        response = await client.chat(messages, **kwargs)
        # Add response to memory
        memory.add("assistant", response)
        return response
    else:
        # Simple completion without memory
        return await client.complete(prompt, system_message, **kwargs)

async def extract(
    prompt: str,
    output_class: Type[T],
    system_message: Optional[str] = None,
    **kwargs
) -> T:
    """
    Extract structured data from the LLM response.

    Args:
        prompt: The question or prompt for the LLM
        output_class: Pydantic model class for the expected output
        system_message: Optional system message/instruction
        **kwargs: Additional parameters for the LLM

    Returns:
        An instance of the output_class
    """
    client = get_llm_client()
    return await client.structured_output(prompt, output_class, system_message, **kwargs)

# =============================================================================
# Compatibility with Original Client
# =============================================================================

class LLMMessageCompat(BaseModel):
    """Compatible message format for backward compatibility."""
    role: str
    content: str

class LLMRequestCompat(BaseModel):
    """Compatible request format for backward compatibility."""
    model: str
    messages: List[LLMMessageCompat]
    temperature: float = Field(default=0.7, ge=0, le=1)
    top_p: float = Field(default=0.9, ge=0, le=1)
    stream: bool = Field(default=False)
    result_format: str = Field(default="message")
    max_tokens: Optional[int] = None
    stop: Optional[List[str]] = None
    frequency_penalty: float = Field(default=0.0)
    presence_penalty: float = Field(default=0.0)

class LLMResponseCompat(BaseModel):
    """Compatible response format for backward compatibility."""
    content: str
    usage: Dict[str, int] = Field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    )
    model: str

class LLMClientCompat:
    """
    Compatibility wrapper for existing LLM client code.

    This class implements the same interface as the original LLMClient,
    but uses the new LLM integration system under the hood.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        """Initialize the compatible LLM client."""
        # Determine provider from the old environment variable naming
        provider = os.environ.get("LLM_PROVIDER", "qwen").lower()
        if provider not in ["qwen", "deepseek"]:
            provider = "openai"  # Default fallback

        self.model = model or os.environ.get("LLM_MODEL", "qwen-7b-chat")
        self.dry_run = dry_run if dry_run is not None else (os.environ.get("LLM_DRY_RUN", "False").lower() == "true")

        # Create the new client
        self.client = get_llm_client(
            provider=provider,
            model=self.model,
            api_key=api_key,
            api_base=base_url
        )

    async def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        task_type: str = "default",
        **kwargs
    ) -> LLMResponseCompat:
        """
        Complete a text prompt using the LLM.

        Args:
            prompt: The text prompt to complete
            system_message: Optional system message for context
            temperature: Sampling temperature (0.0-1.0)
            task_type: Type of task (for dry run responses)
            **kwargs: Additional parameters

        Returns:
            Compatible LLM response
        """
        # Forward to the new client
        response = await self.client.complete(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature,
            **kwargs
        )

        # Convert to compatible format
        return LLMResponseCompat(
            content=response,
            model=self.client.config.model,
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        )

    async def close(self):
        """Placeholder for compatibility."""
        pass

@lru_cache
def create_llm_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    dry_run: Optional[bool] = None
) -> LLMClientCompat:
    """
    Create a compatible LLM client.

    Args:
        base_url: Base URL for the LLM API
        api_key: API key for authentication
        model: Model name to use
        dry_run: Whether to run in dry run mode

    Returns:
        Compatible LLM client
    """
    return LLMClientCompat(
        base_url=base_url,
        api_key=api_key,
        model=model,
        dry_run=dry_run
    )