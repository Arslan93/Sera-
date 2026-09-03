
import os
from dotenv import load_dotenv
from typing import Optional

class Config:
    """
    Handles loading and validation of application configuration from environment variables.
    """
    def __init__(self):
        """
        Initializes the Config object by loading environment variables.
        """
        load_dotenv()
        self.groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
        self.groq_model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.fallback_models: list[str] = [
            self.groq_model,
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b"
        ]
        # Deduplicate while preserving order
        self.fallback_models = list(dict.fromkeys(self.fallback_models))
        self.auto_brief_on_start: bool = os.getenv("AUTO_BRIEF_ON_START", "false").lower() in ("true", "1", "yes")
        self.validate()

    def validate(self):
        """
        Validates the presence of required configuration variables.
        Raises:
            ValueError: If a required environment variable is missing.
        """
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable not found. Please set it in your .env file.")

config = Config()
