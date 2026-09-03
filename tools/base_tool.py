from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """
    Abstract base class for all SERA PC Control Tools.
    """
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool action with given keyword arguments.
        Returns a JSON-serializable result or string.
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """
        Converts the tool definition into OpenAI/Groq compatible function tool schema format.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
