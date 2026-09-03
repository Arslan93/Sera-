
import logging
from abc import ABC, abstractmethod
from typing import List, Iterator, Optional, Any
from groq import Groq
from models.message import Message
from core.config import config

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    @abstractmethod
    def generate_response(self, messages: List[dict], tools: Optional[List[dict]] = None, stream: bool = False) -> Any:
        """
        Generates a response from the LLM.
        Args:
            messages (List[dict]): A list of messages to send to the LLM.
            tools (Optional[List[dict]]): A list of tool schemas available to the LLM.
            stream (bool): Whether to stream the response.
        Returns:
            Any: The response from the LLM, which could be a stream or a full object.
        """
        pass

class GroqProvider(LLMProvider):
    """
    LLM provider for the Groq API with automatic fallback model support.
    """
    def __init__(self, api_key: str, model: str, fallback_models: Optional[List[str]] = None):
        """
        Initializes the GroqProvider.
        Args:
            api_key (str): The Groq API key.
            model (str): The primary Groq model to use.
            fallback_models (Optional[List[str]]): Ordered list of fallback model IDs.
        """
        self.client = Groq(api_key=api_key)
        self.model = model
        self.fallback_models = fallback_models or [model, "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    def generate_response(self, messages: List[dict], tools: Optional[List[dict]] = None, stream: bool = False) -> Any:
        """
        Generates a response from the Groq API, attempting fallback models if the primary model fails.
        """
        models_to_try = [self.model] + [m for m in self.fallback_models if m != self.model]
        last_exception = None

        for attempt_model in models_to_try:
            try:
                request_params = {
                    "messages": messages,
                    "model": attempt_model,
                    "stream": stream,
                }
                if tools:
                    request_params["tools"] = tools
                    request_params["tool_choice"] = "auto"

                logger.info(f"Sending request to Groq with model '{attempt_model}' ({len(tools) if tools else 0} tools).")
                chat_completion = self.client.chat.completions.create(
                    **request_params
                )
                return chat_completion
            except Exception as e:
                last_exception = e
                logger.warning(f"Groq API error on model '{attempt_model}': {e}. Attempting next fallback model...")

        logger.error(f"All models in fallback chain failed: {last_exception}", exc_info=True)
        raise last_exception

def get_llm_client() -> LLMProvider:
    """
    Factory function to get the configured LLM client.
    """
    return GroqProvider(
        api_key=config.groq_api_key,
        model=config.groq_model,
        fallback_models=config.fallback_models
    )

