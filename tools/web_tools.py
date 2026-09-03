import webbrowser
import urllib.parse
import logging
from typing import Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SearchWebTool(BaseTool):
    name = "search_web"
    description = "Searches the web for a query using the default web browser (opens Google search)."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (e.g. 'python tutorials', 'latest AI news')."
            }
        },
        "required": ["query"]
    }

    def execute(self, query: str) -> Dict[str, Any]:
        try:
            encoded_query = urllib.parse.quote_plus(query.strip())
            url = f"https://www.google.com/search?q={encoded_query}"
            webbrowser.open(url)
            logger.info(f"Searched web for: {query}")
            return {"status": "success", "message": f"Opened Google search for '{query}'."}
        except Exception as e:
            logger.error(f"Failed to search web for '{query}': {e}")
            return {"status": "error", "message": f"Could not search web: {str(e)}"}


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = "Opens a specific website or URL in the default web browser."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to open (e.g. 'https://github.com', 'https://youtube.com')."
            }
        },
        "required": ["url"]
    }

    def execute(self, url: str) -> Dict[str, Any]:
        try:
            target_url = url.strip()
            if not target_url.startswith("http://") and not target_url.startswith("https://"):
                target_url = "https://" + target_url

            webbrowser.open(target_url)
            logger.info(f"Opened URL: {target_url}")
            return {"status": "success", "message": f"Opened website '{target_url}'."}
        except Exception as e:
            logger.error(f"Failed to open URL '{url}': {e}")
            return {"status": "error", "message": f"Could not open website: {str(e)}"}
