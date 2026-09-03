import os
import importlib
import inspect
import logging
from pathlib import Path
from typing import List, Dict, Type, Optional
from tools.base_tool import BaseTool
from tools.tool_registry import tool_registry
from skills.base_skill import BaseSkill

logger = logging.getLogger(__name__)

class SkillManager:
    """
    Dynamically loads, registers, and manages permissions/toggles for custom skill plugins.
    """
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or (Path(__file__).parent)
        self.loaded_skills: Dict[str, BaseSkill] = {}
        self.enabled_skills: Dict[str, bool] = {}

    def discover_and_load_skills(self) -> Dict[str, BaseSkill]:
        """Scans the skills directory, loads skill modules, and registers their tools."""
        if not self.skills_dir.exists():
            return {}

        for file_path in self.skills_dir.glob("*.py"):
            if file_path.name.startswith("__") or file_path.name in ["base_skill.py", "skill_manager.py"]:
                continue

            module_name = f"skills.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (inspect.isclass(attr) and 
                        issubclass(attr, BaseSkill) and 
                        attr is not BaseSkill):
                        skill_instance = attr()
                        self.loaded_skills[skill_instance.name] = skill_instance
                        self.enabled_skills[skill_instance.name] = True
                        logger.info(f"Loaded dynamic skill: {skill_instance.name} ({skill_instance.description})")
                        
                        # Auto-register skill tools
                        for tool in skill_instance.get_tools():
                            tool_registry.register_tool(tool)
                            logger.info(f"Auto-registered tool '{tool.name}' from skill '{skill_instance.name}'")
            except Exception as e:
                logger.error(f"Failed to load skill module {module_name}: {e}", exc_info=True)

        return self.loaded_skills

    def enable_skill(self, skill_name: str) -> bool:
        """Enables a loaded skill and registers its tools."""
        skill = self.loaded_skills.get(skill_name)
        if not skill:
            return False

        self.enabled_skills[skill_name] = True
        for tool in skill.get_tools():
            tool_registry.register_tool(tool)
        logger.info(f"Enabled skill '{skill_name}' and registered its tools.")
        return True

    def disable_skill(self, skill_name: str) -> bool:
        """Disables a loaded skill and unregisters its tools for safety/permissions."""
        skill = self.loaded_skills.get(skill_name)
        if not skill:
            return False

        self.enabled_skills[skill_name] = False
        for tool in skill.get_tools():
            tool_registry.unregister_tool(tool.name)
        logger.info(f"Disabled skill '{skill_name}' and unregistered its tools.")
        return True

    def is_skill_enabled(self, skill_name: str) -> bool:
        """Checks if a skill is currently enabled."""
        return self.enabled_skills.get(skill_name, False)

    def get_loaded_skills_summary(self) -> List[Dict[str, Any]]:
        """Returns a list of summaries and permission status for all loaded skills."""
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "enabled": self.enabled_skills.get(skill.name, True),
                "tools": [t.name for t in skill.get_tools()]
            }
            for skill in self.loaded_skills.values()
        ]

skill_manager = SkillManager()
