from abc import ABC, abstractmethod
from typing import List
from tools.base_tool import BaseTool

class BaseSkill(ABC):
    """
    Abstract base class for all SERA skills.
    Skills encapsulate custom domains, external integrations, or specialized capabilities.
    """
    name: str = "custom_skill"
    description: str = "Custom skill description"

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Returns a list of BaseTool instances belonging to this skill."""
        return []
