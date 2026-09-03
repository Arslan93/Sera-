import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Body, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.orchestrator import get_orchestrator, Orchestrator
from tools.tool_registry import tool_registry
from skills.skill_manager import skill_manager
from voice.voice_handler import voice_handler
from voice.wake_word import wake_word_listener

logger = logging.getLogger(__name__)

app = FastAPI(title="SERA AI Interface", version="2.0.0")

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = get_orchestrator()

WEB_DIR = Path(__file__).parent / "web"
assets_dir = WEB_DIR / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

class ChatRequest(BaseModel):
    message: str
    voice: Optional[bool] = False

class LeadRequest(BaseModel):
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    company: Optional[str] = ""
    deal_value: Optional[str] = ""
    status: Optional[str] = "New"
    notes: Optional[str] = ""

class ScaffoldRequest(BaseModel):
    project_type: str
    destination_folder: str
    name: Optional[str] = "App"

class SkillToggleRequest(BaseModel):
    skill_name: str
    enable: bool

# Auto-discover skills on load
skill_manager.discover_and_load_skills()

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = WEB_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Web UI file index.html not found.")
    return FileResponse(index_file)

@app.get("/app.css")
async def serve_css():
    css_file = WEB_DIR / "app.css"
    if not css_file.exists():
        raise HTTPException(status_code=404, detail="app.css not found.")
    return FileResponse(css_file, media_type="text/css")

@app.get("/app.js")
async def serve_js():
    js_file = WEB_DIR / "app.js"
    if not js_file.exists():
        raise HTTPException(status_code=404, detail="app.js not found.")
    return FileResponse(js_file, media_type="application/javascript")

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Executes the orchestrator agentic loop and returns full response & session info."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Run orchestrator turn
        chunks = list(orchestrator.handle_user_message(request.message.strip()))
        full_response = "".join(chunks)

        # Spoken audio if requested
        if request.voice or voice_handler.voice_enabled:
            voice_handler.speak_async(full_response)

        # Get latest message history
        history = orchestrator.memory.get_conversation_history(orchestrator.session_id)
        serialized_history = [
            {
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "name": m.name,
                "created_at": m.created_at
            }
            for m in history
        ]

        return {
            "status": "success",
            "session_id": orchestrator.session_id,
            "response": full_response,
            "history": serialized_history
        }
    except Exception as e:
        logger.error(f"Error in web chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            voice = data.get("voice", False)
            if not message:
                continue

            await websocket.send_json({"type": "state", "state": "thinking"})

            loop = asyncio.get_running_loop()

            def on_tool(tool_name: str, args: dict):
                try:
                    asyncio.run_coroutine_threadsafe(
                        websocket.send_json({"type": "tool_call", "tool": tool_name}),
                        loop
                    )
                except Exception:
                    pass

            full_response = ""
            for chunk in orchestrator.handle_user_message(message, on_tool_call=on_tool):
                full_response += chunk
                await websocket.send_json({"type": "chunk", "content": chunk})

            if voice or voice_handler.voice_enabled:
                await websocket.send_json({"type": "state", "state": "speaking"})
                voice_handler.speak_async(full_response)

            await websocket.send_json({"type": "done", "session_id": orchestrator.session_id})
            await websocket.send_json({"type": "state", "state": "idle"})
    except WebSocketDisconnect:
        logger.info("WebSocket chat client disconnected")
    except Exception as e:
        logger.error(f"WebSocket chat exception: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "error": str(e)})
            await websocket.send_json({"type": "state", "state": "idle"})
        except Exception:
            pass


@app.get("/api/history")
async def get_history():
    """Returns conversation history for current session."""
    history = orchestrator.memory.get_conversation_history(orchestrator.session_id)
    return {
        "session_id": orchestrator.session_id,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "name": m.name,
                "created_at": m.created_at
            }
            for m in history
        ]
    }

@app.post("/api/session/new")
async def new_session():
    """Starts a new conversation session."""
    orchestrator.new_session()
    return {"status": "success", "session_id": orchestrator.session_id}

@app.get("/api/system-info")
async def get_system_info():
    """Returns live hardware metrics (CPU, RAM, Disk, Battery)."""
    res = tool_registry.execute_tool("get_system_info")
    return res

@app.get("/api/skills")
async def get_skills():
    """Returns all loaded dynamic skill plugins and permission states."""
    return {"skills": skill_manager.get_loaded_skills_summary()}

@app.post("/api/skills/toggle")
async def toggle_skill(request: SkillToggleRequest):
    """Enables or disables a specific skill."""
    if request.enable:
        success = skill_manager.enable_skill(request.skill_name)
    else:
        success = skill_manager.disable_skill(request.skill_name)

    if not success:
        raise HTTPException(status_code=404, detail=f"Skill '{request.skill_name}' not found.")
    
    return {
        "status": "success",
        "skill": request.skill_name,
        "enabled": request.enable,
        "skills": skill_manager.get_loaded_skills_summary()
    }

@app.get("/api/leads")
async def get_leads(status: str = "All"):
    """Returns all CRM leads."""
    res = tool_registry.execute_tool("list_leads", filter_status=status)
    return res

@app.post("/api/leads")
async def create_lead(lead: LeadRequest):
    """Creates a new CRM lead."""
    res = tool_registry.execute_tool(
        "create_lead",
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        company=lead.company,
        deal_value=lead.deal_value,
        status=lead.status,
        notes=lead.notes
    )
    return res

@app.get("/api/profile")
async def get_user_profile():
    """Returns user profile and developer preferences."""
    profile_path = Path("data/user_profile.json")
    prefs_path = Path("data/developer_preferences.json")

    profile_data = {}
    prefs_data = {}

    if profile_path.exists():
        try:
            with open(profile_path, "r", encoding="utf-8-sig") as f:
                profile_data = json.load(f)
        except Exception:
            pass

    if prefs_path.exists():
        try:
            with open(prefs_path, "r", encoding="utf-8-sig") as f:
                prefs_data = json.load(f)
        except Exception:
            pass

    return {
        "profile": profile_data,
        "preferences": prefs_data
    }

@app.post("/api/scaffold")
async def scaffold_code(req: ScaffoldRequest):
    """Triggers instant project / component scaffolding."""
    res = tool_registry.execute_tool(
        "scaffold_project",
        project_type=req.project_type,
        destination_folder=req.destination_folder,
        name=req.name
    )
    return res

@app.post("/api/screenshot")
async def take_screenshot():
    """Captures desktop screenshot."""
    res = tool_registry.execute_tool("take_screenshot")
    return res

@app.post("/api/voice/listen")
async def listen_mic():
    """Records speech from microphone and returns transcribed text."""
    try:
        text = voice_handler.record_interactive()
        return {"status": "success", "transcription": text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/voice/toggle")
async def toggle_voice_mode():
    """Toggles spoken response output mode."""
    is_enabled = voice_handler.toggle_voice()
    return {"status": "success", "voice_enabled": is_enabled}

@app.post("/api/wake/toggle")
async def toggle_wake_mode():
    """Toggles background hands-free wake word listener."""
    if wake_word_listener.is_listening:
        wake_word_listener.stop()
        return {"status": "success", "wake_enabled": False}
    else:
        def on_wake():
            logger.info("Wake word detected via web!")
        wake_word_listener.start(on_wake=on_wake)
        return {"status": "success", "wake_enabled": True}

# ═══════════ WEBSOCKET CHAT STREAMING ═══════════
@app.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
                user_msg = data.get("message", "").strip()
                want_voice = data.get("voice", False)
            except Exception:
                user_msg = raw_text.strip()
                want_voice = False

            if not user_msg:
                continue

            full_response = ""
            try:
                for chunk in orchestrator.handle_user_message(user_msg):
                    full_response += chunk
                    await websocket.send_json({"type": "chunk", "content": chunk})

                if want_voice or voice_handler.voice_enabled:
                    voice_handler.speak_async(full_response)

                history = orchestrator.memory.get_conversation_history(orchestrator.session_id)
                serialized = [
                    {
                        "role": m.role,
                        "content": m.content,
                        "tool_calls": m.tool_calls,
                        "name": m.name,
                        "created_at": m.created_at
                    }
                    for m in history
                ]
                await websocket.send_json({
                    "type": "done",
                    "response": full_response,
                    "session_id": orchestrator.session_id,
                    "history": serialized
                })
            except Exception as e:
                logger.error(f"Error streaming chat over WebSocket: {e}", exc_info=True)
                await websocket.send_json({"type": "error", "error": str(e)})
    except WebSocketDisconnect:
        logger.info("Chat WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"Chat WebSocket exception: {e}")

# ═══════════ DAILY BRIEF API ═══════════
@app.get("/api/daily-brief")
async def get_daily_brief_api():
    """Returns freshly aggregated daily orientation brief."""
    from skills.daily_brief_skill import GetDailyBriefTool
    tool = GetDailyBriefTool()
    res = tool.execute(verbose=True)
    return res

# ═══════════ CRM LEAD STATUS UPDATE API ═══════════
class LeadStatusUpdateRequest(BaseModel):
    lead_identifier: str
    status: str
    notes: Optional[str] = None

@app.post("/api/leads/status")
async def update_lead_status_api(req: LeadStatusUpdateRequest):
    """Updates the stage/status of an existing lead."""
    res = tool_registry.execute_tool(
        "update_lead_status",
        lead_identifier=req.lead_identifier,
        new_status=req.status,
        new_notes=req.notes
    )
    return res

# ═══════════ JOB TRACKER APIS ═══════════
@app.get("/api/jobs")
async def get_jobs_api():
    """Returns all job applications."""
    from skills.job_tracker_skill import load_job_applications
    return load_job_applications()

@app.get("/api/jobs/followups")
async def get_job_followups_api(days: int = 7):
    """Returns applications with follow-ups due or overdue."""
    res = tool_registry.execute_tool("list_pending_followups", within_days=days)
    return res

@app.get("/api/jobs/stats")
async def get_job_stats_api():
    """Returns job application funnel stats."""
    res = tool_registry.execute_tool("get_application_stats")
    return res

class JobLogRequest(BaseModel):
    company: str
    role: str
    platform: Optional[str] = "LinkedIn"
    applied_date: Optional[str] = None
    notes: Optional[str] = ""

@app.post("/api/jobs")
async def log_job_api(req: JobLogRequest):
    """Logs a new job application."""
    res = tool_registry.execute_tool(
        "log_application",
        company=req.company,
        role=req.role,
        platform=req.platform,
        applied_date=req.applied_date,
        notes=req.notes
    )
    return res

class JobStageRequest(BaseModel):
    company: str
    stage: str
    notes: Optional[str] = None
    next_followup_date: Optional[str] = None

@app.post("/api/jobs/stage")
async def update_job_stage_api(req: JobStageRequest):
    """Updates the stage and notes of a job application."""
    res = tool_registry.execute_tool(
        "update_application_stage",
        company=req.company,
        stage=req.stage,
        notes=req.notes,
        next_followup_date=req.next_followup_date
    )
    return res

# ═══════════ STUDY SESSION APIS ═══════════
@app.get("/api/study/status")
async def get_study_status_api():
    """Returns current active study session (if any) and recent sessions."""
    from skills.study_session_skill import load_study_sessions
    data = load_study_sessions()
    active_id = data.get("active_session_id")
    sessions = data.get("sessions", [])
    active_session = next((s for s in sessions if s.get("id") == active_id), None)
    return {
        "active_session": active_session,
        "recent_sessions": sessions[-8:]
    }

@app.get("/api/study/stats")
async def get_study_stats_api(days: int = 7):
    """Returns study stats aggregated over recent days."""
    res = tool_registry.execute_tool("get_study_stats", days=days)
    return res

class StudyStartRequest(BaseModel):
    subject: str
    goal: Optional[str] = ""

@app.post("/api/study/start")
async def start_study_api(req: StudyStartRequest):
    """Starts a new study session."""
    res = tool_registry.execute_tool("start_study", subject=req.subject, goal=req.goal)
    return res

class StudyEndRequest(BaseModel):
    notes: Optional[str] = ""

@app.post("/api/study/end")
async def end_study_api(req: StudyEndRequest):
    """Ends the currently active study session."""
    res = tool_registry.execute_tool("end_study", notes=req.notes)
    return res

# ═══════════ CLIPBOARD & READ-LATER APIS ═══════════
@app.get("/api/captures")
async def get_captures_api():
    """Returns all captured clipboard items."""
    from skills.clipboard_capture_skill import load_json_file, CAPTURES_FILE
    return load_json_file(CAPTURES_FILE, "captures")

@app.get("/api/read-later")
async def get_read_later_api():
    """Returns all saved read-later links."""
    from skills.clipboard_capture_skill import load_json_file, READ_LATER_FILE
    return load_json_file(READ_LATER_FILE, "links")

class ReadLaterRequest(BaseModel):
    url: str
    title: Optional[str] = ""

@app.post("/api/read-later")
async def add_read_later_api(req: ReadLaterRequest):
    """Adds a link to read-later."""
    res = tool_registry.execute_tool("add_link_to_read_later", url=req.url, title=req.title)
    return res

@app.get("/api/clipboard/status")
async def get_clipboard_status_api():
    """Returns status of the global clipboard listener."""
    from core.clipboard_listener import clipboard_listener
    return {
        "status": "success",
        "listening": clipboard_listener.is_listening,
        "hotkey": clipboard_listener.hotkey
    }

@app.post("/api/clipboard/toggle")
async def toggle_clipboard_api():
    """Toggles the global clipboard listener on/off."""
    from core.clipboard_listener import clipboard_listener
    if clipboard_listener.is_listening:
        clipboard_listener.stop()
        return {"status": "success", "listening": False}
    else:
        from skills.clipboard_capture_skill import file_captured_content
        started = clipboard_listener.start(on_capture=file_captured_content)
        return {"status": "success", "listening": started}

# ═══════════════════════════════════════════════
# SYSTEM INSIGHTS DIAGNOSTIC ENDPOINTS
# ═══════════════════════════════════════════════

@app.get("/api/system/overview")
async def get_system_overview_api():
    """Returns full hardware, OS, disk, and uptime overview."""
    tool = tool_registry.get_tool("get_pc_overview")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data()
    return {"status": "error", "message": "Overview tool not available"}

@app.get("/api/system/apps")
async def get_system_apps_api(search: str = "", force_refresh: bool = False):
    """Returns list of installed desktop applications."""
    tool = tool_registry.get_tool("list_installed_apps")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data(search=search, force_refresh=force_refresh)
    return {"status": "error", "message": "Installed apps tool not available"}

@app.get("/api/system/games")
async def get_system_games_api(force_refresh: bool = False):
    """Returns list of detected installed games."""
    tool = tool_registry.get_tool("list_installed_games")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data(force_refresh=force_refresh)
    return {"status": "error", "message": "Installed games tool not available"}

@app.get("/api/system/startup")
async def get_system_startup_api():
    """Returns list of Windows startup programs."""
    tool = tool_registry.get_tool("list_startup_programs")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data()
    return {"status": "error", "message": "Startup programs tool not available"}

@app.get("/api/system/processes")
async def get_system_processes_api(sort_by: str = "memory", limit: int = 20):
    """Returns list of running processes sorted by resource usage."""
    tool = tool_registry.get_tool("list_running_processes")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data(sort_by=sort_by, limit=limit)
    return {"status": "error", "message": "Processes tool not available"}

@app.get("/api/system/network")
async def get_system_network_api():
    """Returns network adapters, active connection, and bandwidth stats."""
    tool = tool_registry.get_tool("get_network_info")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data()
    return {"status": "error", "message": "Network info tool not available"}

@app.get("/api/system/battery")
async def get_system_battery_api():
    """Returns detailed battery health and power plan status."""
    tool = tool_registry.get_tool("get_battery_and_power_info")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data()
    return {"status": "error", "message": "Battery info tool not available"}

@app.get("/api/system/account")
async def get_system_account_api():
    """Returns logged-in OS user account metadata."""
    tool = tool_registry.get_tool("get_user_account_info")
    if tool and hasattr(tool, "get_data"):
        return tool.get_data()
    return {"status": "error", "message": "Account info tool not available"}

def run_web_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the Uvicorn web server."""
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")

