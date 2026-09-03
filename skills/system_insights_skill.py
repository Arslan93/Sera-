"""
skills/system_insights_skill.py

System Insights Skill for SERA AI.
Provides comprehensive, strictly read-only PC hardware, OS, installed software,
game libraries, startup programs, running processes, network, battery, and account diagnostics.
"""

import os
import sys
import time
import platform
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any, Optional

import psutil

from skills.base_skill import BaseSkill
from tools.base_tool import BaseTool

# Optional Windows-specific imports
try:
    import winreg
except ImportError:
    winreg = None

try:
    import ctypes
except ImportError:
    ctypes = None


# ═══════════════════════════════════════════════
# IN-MEMORY CACHE HELPER
# ═══════════════════════════════════════════════
_CACHE: Dict[str, Dict[str, Any]] = {}

def get_cached(key: str, ttl_seconds: float) -> tuple:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry["timestamp"] < ttl_seconds):
        return entry["data"], entry["timestamp"]
    return None, None

def set_cached(key: str, data: Any):
    _CACHE[key] = {
        "data": data,
        "timestamp": time.time()
    }


def format_duration(seconds: float) -> str:
    secs = int(seconds)
    days, remainder = divmod(secs, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts) or "< 1m"


# ═══════════════════════════════════════════════
# TOOL 1: GET PC OVERVIEW
# ═══════════════════════════════════════════════
class GetPCOverviewTool(BaseTool):
    name = "get_pc_overview"
    description = "Full hardware and OS overview: CPU, RAM, disk drives, GPU, OS version, uptime, and hostname."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs) -> str:
        data = self.get_data()
        return json.dumps(data, indent=2)

    def get_data(self) -> Dict[str, Any]:
        # OS Info
        os_info = {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.architecture()[0],
            "machine": platform.machine(),
            "platform_string": platform.platform()
        }

        # CPU Info
        cpu_freq = psutil.cpu_freq()
        cpu_info = {
            "processor": platform.processor() or "Unknown CPU",
            "physical_cores": psutil.cpu_count(logical=False) or 1,
            "logical_cores": psutil.cpu_count(logical=True) or 1,
            "current_freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
            "max_freq_mhz": round(cpu_freq.max, 1) if (cpu_freq and cpu_freq.max) else None,
            "usage_percent": psutil.cpu_percent(interval=None)
        }

        # RAM Info
        vm = psutil.virtual_memory()
        ram_info = {
            "total_gb": round(vm.total / (1024 ** 3), 2),
            "used_gb": round(vm.used / (1024 ** 3), 2),
            "available_gb": round(vm.available / (1024 ** 3), 2),
            "percent_used": vm.percent
        }

        # Disk Drives Breakdown
        disks = []
        try:
            partitions = psutil.disk_partitions(all=False)
            for part in partitions:
                if "cdrom" in part.opts or part.fstype == "":
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024 ** 3), 1),
                        "used_gb": round(usage.used / (1024 ** 3), 1),
                        "free_gb": round(usage.free / (1024 ** 3), 1),
                        "percent_used": usage.percent
                    })
                except (PermissionError, OSError):
                    continue
        except Exception:
            pass

        # GPU Info (Graceful fallback)
        gpu_info = "GPU info unavailable"
        if platform.system() == "Windows" and winreg:
            try:
                import subprocess
                res = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"],
                    capture_output=True, text=True, timeout=3
                )
                if res.returncode == 0 and res.stdout.strip():
                    gpus = [g.strip() for g in res.stdout.strip().splitlines() if g.strip()]
                    if gpus:
                        gpu_info = ", ".join(gpus)
            except Exception:
                pass

        # Uptime & Hostname
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time

        try:
            username = os.getlogin()
        except Exception:
            username = os.getenv("USERNAME", "User")

        return {
            "status": "success",
            "hostname": platform.node(),
            "username": username,
            "uptime_seconds": int(uptime_seconds),
            "uptime_human": format_duration(uptime_seconds),
            "os": os_info,
            "cpu": cpu_info,
            "ram": ram_info,
            "disks": disks,
            "gpu": gpu_info
        }


# ═══════════════════════════════════════════════
# TOOL 2: LIST INSTALLED APPS (WITH CACHE)
# ═══════════════════════════════════════════════
class ListInstalledAppsTool(BaseTool):
    CACHE_TTL = 600  # 10 minutes
    name = "list_installed_apps"
    description = "Lists installed desktop applications with version and install date. Results are cached for 10 minutes."
    parameters = {
        "type": "object",
        "properties": {
            "search": {"type": "string", "description": "Optional substring to filter applications by name."},
            "force_refresh": {"type": "boolean", "description": "Bypass cache and force a new registry scan."}
        },
        "required": []
    }

    def execute(self, search: str = "", force_refresh: bool = False, **kwargs) -> str:
        data = self.get_data(search=search, force_refresh=force_refresh)
        return json.dumps(data, indent=2)

    def get_data(self, search: str = "", force_refresh: bool = False) -> Dict[str, Any]:
        cached_data, cached_at = get_cached("installed_apps", self.CACHE_TTL)
        is_from_cache = False
        if cached_data is not None and not force_refresh:
            apps = cached_data
            scan_age = int(time.time() - cached_at)
            is_from_cache = True
        else:
            apps = self._scan_installed_apps()
            set_cached("installed_apps", apps)
            scan_age = 0

        if search:
            q = search.lower()
            filtered = [a for a in apps if q in a["name"].lower() or q in (a.get("publisher") or "").lower()]
        else:
            filtered = apps

        return {
            "status": "success",
            "total_apps": len(apps),
            "returned_count": len(filtered),
            "cached": is_from_cache,
            "cache_age_seconds": scan_age,
            "apps": filtered
        }

    def _scan_installed_apps(self) -> List[Dict[str, Any]]:
        apps_map = {}
        if not winreg:
            return []

        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for root_key, sub_key in registry_paths:
            try:
                with winreg.OpenKey(root_key, sub_key) as key:
                    num_subkeys, _, _ = winreg.QueryInfoKey(key)
                    for i in range(num_subkeys):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as app_key:
                                try:
                                    name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                                except FileNotFoundError:
                                    continue

                                if not name or not str(name).strip():
                                    continue
                                name_clean = str(name).strip()

                                # Filter out Windows update patches or GUID noise
                                if name_clean.startswith("KB") and len(name_clean) < 12:
                                    continue

                                try:
                                    version, _ = winreg.QueryValueEx(app_key, "DisplayVersion")
                                except FileNotFoundError:
                                    version = ""

                                try:
                                    publisher, _ = winreg.QueryValueEx(app_key, "Publisher")
                                except FileNotFoundError:
                                    publisher = ""

                                try:
                                    install_date, _ = winreg.QueryValueEx(app_key, "InstallDate")
                                except FileNotFoundError:
                                    install_date = ""

                                # Deduplicate by lowercase name
                                key_str = name_clean.lower()
                                if key_str not in apps_map:
                                    apps_map[key_str] = {
                                        "name": name_clean,
                                        "version": str(version).strip() if version else "",
                                        "publisher": str(publisher).strip() if publisher else "",
                                        "install_date": str(install_date).strip() if install_date else ""
                                    }
                        except (PermissionError, OSError):
                            continue
            except (PermissionError, OSError, FileNotFoundError):
                continue

        return sorted(apps_map.values(), key=lambda a: a["name"].lower())


# ═══════════════════════════════════════════════
# TOOL 3: LIST INSTALLED GAMES
# ═══════════════════════════════════════════════
class ListInstalledGamesTool(BaseTool):
    CACHE_TTL = 600  # 10 minutes
    name = "list_installed_games"
    description = "Detects installed games from common platforms (Steam, Epic Games, Riot). Cached for 10 minutes."
    parameters = {
        "type": "object",
        "properties": {
            "force_refresh": {"type": "boolean", "description": "Bypass cache and force rescan."}
        },
        "required": []
    }

    def execute(self, force_refresh: bool = False, **kwargs) -> str:
        data = self.get_data(force_refresh=force_refresh)
        return json.dumps(data, indent=2)

    def get_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        cached_data, cached_at = get_cached("installed_games", self.CACHE_TTL)
        is_from_cache = False
        if cached_data is not None and not force_refresh:
            games = cached_data
            scan_age = int(time.time() - cached_at)
            is_from_cache = True
        else:
            games = self._scan_games()
            set_cached("installed_games", games)
            scan_age = 0

        return {
            "status": "success",
            "total_games": len(games),
            "cached": is_from_cache,
            "cache_age_seconds": scan_age,
            "games": games,
            "message": "Found installed games" if games else "No game launchers or installed games detected on this system"
        }

    def _scan_games(self) -> List[Dict[str, Any]]:
        games = []

        # 1. Steam Detection
        steam_paths = [
            Path(r"C:\Program Files (x86)\Steam"),
            Path(r"C:\Program Files\Steam"),
            Path(r"D:\Steam"),
            Path(r"E:\Steam")
        ]
        if winreg:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as sk:
                    sp, _ = winreg.QueryValueEx(sk, "SteamPath")
                    if sp:
                        steam_paths.insert(0, Path(sp))
            except Exception:
                pass

        steam_library_folders = []
        for sp in steam_paths:
            if sp.exists():
                steam_library_folders.append(sp)
                vdf = sp / "steamapps" / "libraryfolders.vdf"
                if vdf.exists():
                    try:
                        content = vdf.read_text(encoding="utf-8", errors="ignore")
                        for line in content.splitlines():
                            if '"path"' in line:
                                parts = line.split('"')
                                if len(parts) >= 4:
                                    lib_path = Path(parts[3].replace(r"\\", "\\"))
                                    if lib_path.exists() and lib_path not in steam_library_folders:
                                        steam_library_folders.append(lib_path)
                    except Exception:
                        pass
                break

        for lib in steam_library_folders:
            steamapps = lib / "steamapps"
            if steamapps.exists():
                for acf in steamapps.glob("appmanifest_*.acf"):
                    try:
                        name = None
                        size = None
                        for line in acf.read_text(encoding="utf-8", errors="ignore").splitlines():
                            line_strip = line.strip()
                            if line_strip.startswith('"name"'):
                                parts = line_strip.split('"')
                                if len(parts) >= 4:
                                    name = parts[3]
                            elif line_strip.startswith('"SizeOnDisk"'):
                                parts = line_strip.split('"')
                                if len(parts) >= 4 and parts[3].isdigit():
                                    size = round(int(parts[3]) / (1024 ** 3), 1)
                        if name and name != "Steamworks Common Redistributables":
                            games.append({
                                "name": name,
                                "platform": "Steam",
                                "install_path": str(lib),
                                "size_gb": size or 0
                            })
                    except Exception:
                        continue

        # 2. Epic Games Detection
        epic_manifest_dir = Path(r"C:\ProgramData\Epic\EpicGamesLauncher\Data\Manifests")
        if epic_manifest_dir.exists():
            for item in epic_manifest_dir.glob("*.item"):
                try:
                    data = json.loads(item.read_text(encoding="utf-8", errors="ignore"))
                    name = data.get("DisplayName")
                    location = data.get("InstallLocation")
                    size_bytes = data.get("InstallSize") or 0
                    if name:
                        games.append({
                            "name": name,
                            "platform": "Epic Games",
                            "install_path": location or "",
                            "size_gb": round(size_bytes / (1024 ** 3), 1)
                        })
                except Exception:
                    continue

        return sorted(games, key=lambda g: g["name"].lower())


# ═══════════════════════════════════════════════
# TOOL 4: LIST STARTUP PROGRAMS
# ═══════════════════════════════════════════════
class ListStartupProgramsTool(BaseTool):
    name = "list_startup_programs"
    description = "Lists programs configured to run at Windows startup from Registry Run keys and Startup folder."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs) -> str:
        data = self.get_data()
        return json.dumps(data, indent=2)

    def get_data(self) -> Dict[str, Any]:
        programs = []

        if winreg:
            registry_targets = [
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "User Registry (HKCU)"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "System Registry (HKLM)"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Run", "32-bit Registry (HKLM)")
            ]
            for root_key, sub_key, loc_label in registry_targets:
                try:
                    with winreg.OpenKey(root_key, sub_key) as key:
                        num_values = winreg.QueryInfoKey(key)[1]
                        for i in range(num_values):
                            try:
                                name, val, _ = winreg.EnumValue(key, i)
                                if name:
                                    programs.append({
                                        "name": name,
                                        "command": str(val).strip(),
                                        "location": loc_label,
                                        "enabled": True
                                    })
                            except (PermissionError, OSError):
                                continue
                except (PermissionError, OSError, FileNotFoundError):
                    continue

        # Startup Folders
        startup_dirs = [
            (Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")), "User Startup Folder"),
            (Path(os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup")), "Common Startup Folder")
        ]
        for sdir, loc_label in startup_dirs:
            if sdir.exists():
                for f in sdir.iterdir():
                    if f.is_file() and f.name != "desktop.ini":
                        programs.append({
                            "name": f.stem,
                            "command": str(f),
                            "location": loc_label,
                            "enabled": True
                        })

        return {
            "status": "success",
            "total_startup_programs": len(programs),
            "programs": programs
        }


# ═══════════════════════════════════════════════
# TOOL 5: LIST RUNNING PROCESSES
# ═══════════════════════════════════════════════
class ListRunningProcessesTool(BaseTool):
    name = "list_running_processes"
    description = "Lists currently running processes with resource usage sorted by CPU or memory."
    parameters = {
        "type": "object",
        "properties": {
            "sort_by": {"type": "string", "enum": ["cpu", "memory"], "description": "Sort metric (default: memory)."},
            "limit": {"type": "integer", "description": "Max number of processes to return (default: 20)."}
        },
        "required": []
    }

    def execute(self, sort_by: str = "memory", limit: int = 20, **kwargs) -> str:
        data = self.get_data(sort_by=sort_by, limit=limit)
        return json.dumps(data, indent=2)

    def get_data(self, sort_by: str = "memory", limit: int = 20) -> Dict[str, Any]:
        processes = []
        sort_metric = sort_by.lower() if sort_by in ("cpu", "memory") else "memory"

        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                info = p.info
                mem_mb = round((info['memory_info'].rss if info['memory_info'] else 0) / (1024 * 1024), 1)
                cpu_p = info['cpu_percent'] or 0.0

                processes.append({
                    "pid": info['pid'],
                    "name": info['name'] or "Unknown",
                    "cpu_percent": round(cpu_p, 1),
                    "memory_mb": mem_mb,
                    "is_high_resource": (cpu_p > 40.0) or (mem_mb > 1500.0)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if sort_metric == "cpu":
            processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
        else:
            processes.sort(key=lambda x: x["memory_mb"], reverse=True)

        return {
            "status": "success",
            "sort_by": sort_metric,
            "total_processes": len(processes),
            "returned_count": min(len(processes), limit),
            "processes": processes[:limit]
        }


# ═══════════════════════════════════════════════
# TOOL 6: GET NETWORK INFO
# ═══════════════════════════════════════════════
class GetNetworkInfoTool(BaseTool):
    PUBLIC_IP_TTL = 3600  # 1 hour
    name = "get_network_info"
    description = "Current network status: adapters, IP addresses, connection type, public IP, and bandwidth stats."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs) -> str:
        data = self.get_data()
        return json.dumps(data, indent=2)

    def get_data(self) -> Dict[str, Any]:
        adapters = []
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        active_adapter = None

        for name, addr_list in addrs.items():
            stat = stats.get(name)
            is_up = stat.isup if stat else False
            ipv4 = None
            mac = None

            for a in addr_list:
                if a.family == 2:  # AF_INET (IPv4)
                    ipv4 = a.address
                elif hasattr(psutil, 'AF_LINK') and a.family == psutil.AF_LINK:
                    mac = a.address

            is_wifi = "wi-fi" in name.lower() or "wlan" in name.lower() or "wireless" in name.lower()

            item = {
                "name": name,
                "is_up": is_up,
                "type": "Wi-Fi" if is_wifi else "Ethernet",
                "ipv4": ipv4 or "None",
                "mac": mac or "Unknown",
                "speed_mbps": stat.speed if stat else 0
            }
            adapters.append(item)

            if is_up and ipv4 and not ipv4.startswith("127."):
                if not active_adapter:
                    active_adapter = item

        # IO Counters
        io = psutil.net_io_counters()
        bandwidth = {
            "bytes_sent_mb": round(io.bytes_sent / (1024 * 1024), 1),
            "bytes_recv_mb": round(io.bytes_recv / (1024 * 1024), 1)
        }

        # Cached Public IP
        cached_ip, _ = get_cached("public_ip", self.PUBLIC_IP_TTL)
        if cached_ip is None:
            cached_ip = self._fetch_public_ip()
            set_cached("public_ip", cached_ip)

        return {
            "status": "success",
            "active_adapter": active_adapter,
            "adapters": adapters,
            "bandwidth": bandwidth,
            "public_ip": cached_ip
        }

    def _fetch_public_ip(self) -> str:
        try:
            req = urllib.request.Request("https://api.ipify.org?format=json", headers={"User-Agent": "SERA-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("ip", "Unavailable")
        except Exception:
            return "Unavailable"


# ═══════════════════════════════════════════════
# TOOL 7: GET BATTERY AND POWER INFO
# ═══════════════════════════════════════════════
class GetBatteryAndPowerInfoTool(BaseTool):
    name = "get_battery_and_power_info"
    description = "Battery charge, power plugged status, and battery health telemetry for portable systems."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs) -> str:
        data = self.get_data()
        return json.dumps(data, indent=2)

    def get_data(self) -> Dict[str, Any]:
        bat = psutil.sensors_battery()
        if bat is None:
            return {
                "status": "success",
                "has_battery": False,
                "message": "No battery detected (Desktop system)"
            }

        power_unlimited = getattr(psutil, 'POWER_TIME_UNLIMITED', -1)
        power_unknown = getattr(psutil, 'POWER_TIME_UNKNOWN', -2)
        secs_left = bat.secsleft if (bat.secsleft != power_unlimited and bat.secsleft != power_unknown and bat.secsleft is not None and bat.secsleft > 0) else None
        time_remaining_str = format_duration(secs_left) if secs_left and secs_left > 0 else "Calculating / Plugged in"

        return {
            "status": "success",
            "has_battery": True,
            "percent": round(bat.percent, 1),
            "power_plugged": bat.power_plugged,
            "seconds_remaining": secs_left,
            "time_remaining_human": time_remaining_str
        }


# ═══════════════════════════════════════════════
# TOOL 8: GET USER ACCOUNT INFO
# ═══════════════════════════════════════════════
class GetUserAccountInfoTool(BaseTool):
    name = "get_user_account_info"
    description = "Metadata about the logged-in OS user account: username, admin privileges, home directory (read-only)."
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }

    def execute(self, **kwargs) -> str:
        data = self.get_data()
        return json.dumps(data, indent=2)

    def get_data(self) -> Dict[str, Any]:
        try:
            username = os.getlogin()
        except Exception:
            username = os.getenv("USERNAME", "User")

        # Admin check
        is_admin = False
        if platform.system() == "Windows" and ctypes:
            try:
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            except Exception:
                pass
        elif hasattr(os, "getuid"):
            is_admin = (os.getuid() == 0)

        home_dir = str(Path.home())

        return {
            "status": "success",
            "username": username,
            "is_administrator": is_admin,
            "account_type": "Administrator" if is_admin else "Standard User",
            "home_directory": home_dir,
            "os_node": platform.node()
        }


# ═══════════════════════════════════════════════
# SYSTEM INSIGHTS SKILL
# ═══════════════════════════════════════════════
class SystemInsightsSkill(BaseSkill):
    name = "system_insights"
    description = "Comprehensive read-only PC hardware, software, network, battery, and OS diagnostics."

    def __init__(self):
        self._overview_tool = GetPCOverviewTool()
        self._apps_tool = ListInstalledAppsTool()
        self._games_tool = ListInstalledGamesTool()
        self._startup_tool = ListStartupProgramsTool()
        self._processes_tool = ListRunningProcessesTool()
        self._network_tool = GetNetworkInfoTool()
        self._battery_tool = GetBatteryAndPowerInfoTool()
        self._account_tool = GetUserAccountInfoTool()

    def get_tools(self) -> List[BaseTool]:
        return [
            self._overview_tool,
            self._apps_tool,
            self._games_tool,
            self._startup_tool,
            self._processes_tool,
            self._network_tool,
            self._battery_tool,
            self._account_tool
        ]

    def get_system_prompt_addition(self) -> Optional[str]:
        return (
            "System Insights Diagnostic Tools:\n"
            "- Use `get_pc_overview` for hardware specs, multi-drive storage breakdown, CPU/RAM, and OS info.\n"
            "- Use `list_installed_apps` to inspect installed software.\n"
            "- Use `list_installed_games` to find Steam and Epic games installed on the PC.\n"
            "- Use `list_startup_programs` to inspect programs launching at boot.\n"
            "- Use `list_running_processes` to check resource-heavy applications.\n"
            "- Use `get_network_info` for adapters, connection type, bandwidth, and public IP.\n"
            "- Use `get_battery_and_power_info` for battery health.\n"
            "- Use `get_user_account_info` for OS user account metadata."
        )
