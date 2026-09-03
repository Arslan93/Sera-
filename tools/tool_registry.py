import logging
from typing import Dict, List, Any, Optional
from tools.base_tool import BaseTool
from tools.app_tools import OpenAppTool, CloseAppTool
from tools.file_tools import (
    OpenFileTool, OpenFolderTool, ListFilesTool, SearchFileTool,
    WriteFileTool, ReadFileTool, DeleteFileTool, MoveFileTool
)
from tools.coding_tools import ExecuteCodeTool, EditFileTool
from tools.web_tools import SearchWebTool, OpenUrlTool
from tools.system_tools import GetSystemInfoTool
from tools.screenshot_tools import TakeScreenshotTool

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Central registry for all PC control and coding tools available to SERA.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Registers a tool instance into the registry."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def unregister_tool(self, name: str) -> bool:
        """Removes a tool from the registry."""
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Retrieves a tool by its name."""
        return self._tools.get(name)

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Returns JSON schema definitions for all registered tools."""
        return [tool.to_schema() for tool in self._tools.values()]

    def execute_tool(self, _tool_name: str, /, **kwargs) -> Any:
        """Executes a registered tool by name with arguments."""
        tool = self.get_tool(_tool_name)
        if not tool:
            err_msg = f"Tool '{_tool_name}' is not registered."
            logger.warning(err_msg)
            return {"status": "error", "message": err_msg}

        try:
            logger.info(f"Executing tool '{_tool_name}' with params: {kwargs}")
            return tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool '{_tool_name}': {e}", exc_info=True)
            return {"status": "error", "message": f"Execution failed for tool '{_tool_name}': {str(e)}"}

def get_default_tool_registry() -> ToolRegistry:
    """Factory creating a ToolRegistry populated with all tools."""
    registry = ToolRegistry()
    registry.register_tool(OpenAppTool())
    registry.register_tool(CloseAppTool())
    registry.register_tool(OpenFileTool())
    registry.register_tool(OpenFolderTool())
    registry.register_tool(ListFilesTool())
    registry.register_tool(SearchFileTool())
    registry.register_tool(WriteFileTool())
    registry.register_tool(ReadFileTool())
    registry.register_tool(DeleteFileTool())
    registry.register_tool(MoveFileTool())
    registry.register_tool(ExecuteCodeTool())
    registry.register_tool(EditFileTool())
    registry.register_tool(SearchWebTool())
    registry.register_tool(OpenUrlTool())
    registry.register_tool(GetSystemInfoTool())
    registry.register_tool(TakeScreenshotTool())
    return registry

tool_registry = get_default_tool_registry()
