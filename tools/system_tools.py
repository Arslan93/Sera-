import psutil
import logging
from typing import Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Gets real-time computer hardware statistics including CPU usage, RAM memory usage, Disk space, and Battery status."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self) -> Dict[str, Any]:
        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=0.2)
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)

            # Memory (RAM)
            mem = psutil.virtual_memory()
            ram_info = {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent_used": mem.percent
            }

            # Disk
            disk = psutil.disk_usage('/')
            disk_info = {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": disk.percent
            }

            # Battery (if available)
            battery = psutil.sensors_battery()
            battery_info = None
            if battery:
                battery_info = {
                    "percent": battery.percent,
                    "power_plugged": battery.power_plugged,
                    "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Plugged In"
                }

            result = {
                "status": "success",
                "cpu": {
                    "usage_percent": f"{cpu_percent}%",
                    "physical_cores": cpu_count_physical,
                    "logical_threads": cpu_count_logical
                },
                "ram": ram_info,
                "disk": disk_info,
                "battery": battery_info or "No battery detected (Desktop)"
            }
            logger.info("Retrieved system info successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"status": "error", "message": f"Could not retrieve system info: {str(e)}"}
