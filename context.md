# SERA — Technical Architecture, Implementation & Context Document

> **Target Audience:** AI Assistants, LLM Agents, and Software Engineers.  
> **Document Purpose:** Complete, self-contained architectural context for understanding, maintaining, extending, and operating **SERA (Personal AI Desktop Assistant)**.

---

## 1. Project Overview & Identity

- **Project Name:** SERA (Personal AI Desktop Assistant & Coding Companion)
- **Primary Objective:** A fast, low-latency, free-tier desktop AI assistant capable of conversational reasoning, PC automation (opening apps, managing files, inspecting system metrics, web searches, capturing screenshots), and cross-language coding assistance.
- **Operating System:** Windows (with cross-platform abstraction design).
- **Core Technology Stack:**
  - **Language:** Python 3.11+ / 3.14
  - **Frontend Architecture:** React 18, Vite, Tailwind CSS, Lucide React
  - **Web Framework:** FastAPI + Uvicorn + WebSockets
  - **LLM Provider:** Groq API (High throughput / low latency inference)
  - **Active Default Model:** `openai/gpt-oss-120b` (with `llama-3.3-70b-versatile` fallback)
  - **Persistence:** Local SQLite database (`data/sera.db`) + Atomic JSON datastores
  - **CLI Interface:** Rich Terminal UI (`interfaces/terminal.py`)
  - **PC Automation Libraries:** `psutil`, `pyautogui`, `subprocess`, `webbrowser`, `pathlib`, `keyboard`, `pyperclip`
  - **Voice Engine:** Groq Whisper STT + Microsoft Edge Neural TTS (`edge-tts`)
  - **Test Framework:** `pytest` (77 passing automated tests)

---

## 2. Milestone Roadmap & Implementation State

| Phase | Description | Status | Deliverables & Features |
|---|---|---|---|
| **Phase 1** | **Core Brain + Text Chat** | 🟢 **Complete** | Groq streaming client, SQLite session memory, UTF-8 Rich CLI interface, session commands (`/help`, `/new`, `/history`, `/clear`, `/exit`). |
| **Phase 2** | **PC Control (Tools Layer)** | 🟢 **Complete** | Tool Registry, OpenAI/Groq function calling schema engine, App launch/close, Deep File/Folder search, Web search, Hardware stats, Screenshots. |
| **Phase 3** | **Voice Layer** | 🟢 **Complete** | Groq Whisper STT (`whisper-large-v3-turbo`), Microsoft `edge-tts` neural synthesis, `/voice` TTS toggle, `/mic` interactive speech input. |
| **Phase 4** | **Coding Assistant + Sandbox** | 🟢 **Complete** | Sandboxed subprocess code runner (`execute_code`), targeted file editor (`edit_file`), direct file reader/writer (`read_file`, `write_file`), automated self-debug loop. |
| **Phase 5** | **Wake Word & Extensible Skills**| 🟢 **Complete** | Hands-free "Hey Sera" wake word background listener (`/wake`), dynamic modular skill plugin engine (`skills/`), built-in quick notes skill (`/skills`). |
| **Phase 6** | **Daylight React.js Command Center** | 🟢 **Complete** | Full React 18 SPA (`frontend/`), 3D hardware dials, AI State Orb, `Ctrl+K` palette, WebSocket streaming, and 77/77 passing tests. |

---

## 3. Directory Structure

```text
Jarvis/
├── ARCHITECTURE.md           # System architecture, component layers & sequence diagrams
├── README.md                 # User-facing manual, quickstart guide & commands
├── context.md                # Exhaustive AI agent context & historical implementation log
├── main.py                   # Master entrypoint for CLI & Web Dashboard
├── requirements.txt          # Python virtual environment dependencies
├── frontend/                 # React 18 SPA source code
│   ├── package.json
│   ├── vite.config.js        # Output to ../interfaces/web and proxy to FastAPI (:8000)
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx          # React DOM root
│       ├── App.jsx           # Main workbench layout
│       ├── index.css         # Tailwind directives, 3D radial dials & orb lighting
│       ├── context/          # Central AppContext (WebSocket, telemetry, toasts, session)
│       └── components/       # Reusable components & 5 modular workbench views
├── core/
│   ├── config.py             # Environment config loader (.env), model settings & validation
│   ├── llm_client.py         # Abstract LLMProvider interface & GroqProvider implementation
│   ├── orchestrator.py       # Central pipeline: handles user turn, memory, tool dispatch & streaming
│   └── clipboard_listener.py # Global hotkey (Ctrl+Shift+S) background listener daemon
├── memory/
│   ├── database.py           # SQLite connection manager, auto-migrations & schema setup
│   └── memory_store.py       # CRUD operations for sessions and messages with deterministic ordering
├── interfaces/
│   ├── terminal.py           # Rich-based interactive terminal chat loop & slash-command dispatcher
│   ├── web_server.py         # FastAPI REST + WebSocket + Static server exposing all AI & PC capabilities
│   └── web/                  # Compiled production React build (served by FastAPI at :8000)
├── models/
│   └── message.py            # Message dataclass (role, content, session_id, tool_calls, tool_call_id, name)
├── tools/
│   ├── __init__.py           # Exports BaseTool, ToolRegistry, default tool_registry instance
│   ├── base_tool.py          # Abstract BaseTool class (name, description, schema, execute)
│   ├── tool_registry.py      # Registry for dynamic tool discovery, unregistration & JSON Schema export
│   ├── pc_control_tools.py   # Desktop automation (open_app, close_app, list_files, search_file, open_file, open_folder)
│   ├── web_tools.py          # Web intelligence (search_web via duckduckgo, open_url)
│   ├── system_tools.py       # Hardware metrics (get_system_info) & visual captures (take_screenshot)
│   ├── coding_tools.py       # Subprocess code runner (execute_code) & surgical file editor (edit_file)
│   └── file_tools.py         # Direct disk tools (write_file, read_file, delete_file, move_file)
├── voice/
│   ├── tts.py                # Microsoft edge-tts neural voice synthesis, markdown text cleaner & sounddevice playback
│   ├── stt.py                # Microphone audio recorder (16kHz WAV) & Groq Whisper API transcription
│   ├── wake_word.py          # Background 'Hey Sera' wake word detection & activation thread
│   └── voice_handler.py      # Unified Voice coordinator with /voice toggling & interactive mic listening
├── skills/
│   ├── __init__.py           # Exports BaseSkill, SkillManager
│   ├── base_skill.py         # Abstract BaseSkill plugin interface
│   ├── skill_manager.py      # Dynamic skill auto-discovery and tool registration engine
│   ├── notes_skill.py        # Built-in quick personal note-taking skill (add_note, list_notes) with subject tagging
│   ├── dev_workflow_skill.py # Arslan's full-stack developer skill (scaffold_project, get_dev_preferences)
│   ├── crm_skill.py          # Business CRM automation skill (create_lead, list_leads, update_lead_status)
│   ├── daily_brief_skill.py  # Daily orientation briefing aggregator (get_daily_brief, once-per-day state gating)
│   ├── study_session_skill.py # RGPV exam prep & study manager (start_study, end_study, quiz_me, get_study_stats)
│   ├── job_tracker_skill.py  # Job/internship search pipeline manager (log_application, update_application_stage, list_pending_followups, get_application_stats)
│   └── clipboard_capture_skill.py # Global clipboard auto-classifier & filer (process_clipboard_capture, add_link_to_read_later)
├── prompts/
│   └── system_prompt.txt     # System instructions defining SERA's identity, PC control, coding & self-debugging
├── data/
│   ├── sera.db               # SQLite database file (stores sessions and conversation turns)
│   ├── notes.json            # JSON storage for NotesSkill
│   ├── leads.json            # JSON storage for CRMSkill
│   ├── study_sessions.json   # JSON storage for StudySessionSkill
│   ├── job_applications.json # JSON storage for JobTrackerSkill
│   ├── captures.json         # JSON audit log for ClipboardCaptureSkill
│   ├── read_later.json       # JSON storage for saved URLs/links
│   ├── state.json            # Application state tracking (e.g., last_brief_date)
│   ├── user_profile.json     # Permanent profile for Arslan Ali Mansoori (skills, experience, projects)
│   └── developer_preferences.json # Code standards & stack preferences (React, Node, Express, MongoDB, Python, Tailwind)
├── logs/
│   └── sera.log              # Rotating application runtime log file
├── screenshots/              # Output directory for screenshots taken by TakeScreenshotTool
├── tests/
│   ├── __init__.py
│   ├── test_phase1.py        # Automated test suite for Phase 1 (memory, orchestrator, terminal UI)
│   ├── test_phase2.py        # Automated test suite for Phase 2 (all 10 tools & multi-step agentic loop)
│   ├── test_phase3.py        # Automated test suite for Phase 3 (TTS, STT, VoiceHandler & commands)
│   ├── test_phase4.py        # Automated test suite for Phase 4 (ExecuteCodeTool, EditFileTool, self-debug loop)
│   ├── test_phase5.py        # Automated test suite for Phase 5 (Skills plugin engine & WakeWordListener)
│   ├── test_e2e_integration.py # End-to-end integration test suite (agentic loops, safety caps, fallback models)
│   ├── test_web_server.py    # Automated test suite for FastAPI Web Server & API endpoints
│   ├── test_daily_brief.py   # Automated test suite for Daily Brief skill, gating & client tracker integration
│   ├── test_study_session.py # Automated test suite for Study Session skill, timers, quiz retrieval & stats
│   ├── test_job_tracker.py   # Automated test suite for Job Tracker skill, fuzzy update, followups & stats
│   └── test_clipboard_capture.py # Automated test suite for Clipboard capture, debounce & classification heuristics
├── .env                      # Local secret variables (GROQ_API_KEY, GROQ_MODEL)
├── .env.example              # Template environment configuration
├── requirements.txt          # Production & testing dependencies
├── main.py                   # Main executable entrypoint
├── README.md                 # Project documentation
└── context.md                # THIS comprehensive technical context document
```

---

## 4. Detailed Component & Code Specifications

### 4.1. Core Engine (`core/`)

#### `core/config.py`
- **Class `Config`**:
  - Automatically invokes `dotenv.load_dotenv()`.
  - Attributes:
    - `groq_api_key`: Reads `GROQ_API_KEY` from environment.
    - `groq_model`: Defaults to `openai/gpt-oss-120b`.
  - `validate()`: Enforces that `GROQ_API_KEY` is non-empty, raising a clear `ValueError` if missing.

#### `core/llm_client.py`
- **Abstract Class `LLMProvider`**:
  - Defines `generate_response(messages: List[dict], tools: Optional[List[dict]] = None, stream: bool = False) -> Any`.
- **Class `GroqProvider(LLMProvider)`**:
  - Wraps official `groq.Groq` client.
  - Dynamically injects `tools` array and `tool_choice="auto"` when tool schemas are supplied.
  - Supports both full object completion (needed for parsing tool calls) and iterator streaming chunks (for user-facing low-latency output).

#### `core/orchestrator.py`
- **Class `Orchestrator`**:
  - Central coordinator linking LLM, memory, tools, and UI.
  - `__init__(llm_client, memory, tool_registry, system_prompt)`:
    - Automatically creates a new session in SQLite memory upon initialization (`self.session_id`).
  - `handle_user_message(user_message: str) -> Iterator[str]`:
    1. Saves incoming user message to SQLite memory.
    2. Fetches recent conversation history (`self.memory.get_conversation_history`).
    3. Formats messages into OpenAI-compatible dictionaries including past tool calls and outputs.
    4. Obtains tool schemas from `self.tool_registry.get_tool_schemas()`.
    5. If tools exist: queries LLM with `stream=False` to detect potential function calls.
    6. If `response_message.tool_calls` is present:
       - Saves assistant tool call message to memory.
       - Dispatches each tool call via `self._execute_tool_calls(tool_calls)`.
       - Saves tool execution output with `role="tool"`, `tool_call_id`, and `name`.
       - Re-prompts the LLM with the updated history (including tool responses) using `stream=True`.
       - Streams the final natural language answer to the user while capturing it into memory.
    7. If no tool calls: streams response directly to user and saves to memory.
  - `new_session()`: Starts a clean session ID.
  - `get_orchestrator(tool_registry=None)`: Factory function returning ready-to-run Orchestrator.

---

### 4.2. Memory & Persistence (`memory/`)

#### `memory/database.py`
- **Class `Database`**:
  - Manages SQLite connection via context manager `get_connection()` with automatic commits/rollbacks and row factories.
  - `create_tables()`:
    - Table `sessions`: `id` (PK), `created_at`, `updated_at`.
    - Table `messages`: `id` (PK), `session_id` (FK), `role`, `content`, `tool_calls` (JSON), `tool_call_id`, `name`, `created_at`.
    - **Self-Healing Auto-Migration**: Checks existing PRAGMA table columns and automatically executes `ALTER TABLE` if any column (`tool_calls`, `tool_call_id`, `name`) is missing from older databases.

#### `memory/memory_store.py`
- **Class `MemoryStore`**:
  - `create_session() -> int`: Creates session record and returns `lastrowid`.
  - `save_message(message: Message)`: Serializes tool call structures into JSON and inserts message row.
  - `get_conversation_history(session_id: int, limit: int = 20) -> List[Message]`:
    - Executes `ORDER BY id DESC LIMIT ?` and reverses the result, ensuring deterministic, strict chronological ordering even for rapid messages.

---

### 4.3. PC Control Tools Layer (`tools/`)

#### `tools/base_tool.py`
- **Class `BaseTool(ABC)`**:
  - Attributes: `name` (str), `description` (str), `parameters` (dict - JSON schema).
  - `to_schema() -> dict`: Converts tool definition into `{ "type": "function", "function": { ... } }`.
  - `execute(**kwargs) -> Any`: Abstract execution method.

#### Registered Tools Inventory:
1. **`OpenAppTool` (`open_app`)**:
   - Opens desktop software. Includes dictionary of Windows known apps (`notepad`, `calculator`/`calc`, `paint`, `chrome`, `edge`, `code`/`vscode`, `cmd`, `powershell`, `explorer`, `taskmgr`, `spotify`).
   - Uses `os.startfile` and `subprocess.Popen`.
2. **`CloseAppTool` (`close_app`)**:
   - Iterates processes via `psutil.process_iter` matching process names and terminates them safely.
3. **`OpenFolderTool` (`open_folder`)**:
   - Opens directories in Windows Explorer. Handles shortcuts (`downloads`, `documents`, `desktop`, `pictures`, `music`, `videos`, `home`) or absolute paths.
4. **`OpenFileTool` (`open_file`)**:
   - Opens specific files with their default associated system app.
5. **`ListFilesTool` (`list_files`)**:
   - Lists files and subfolders in user directories with file size and type.
6. **`SearchFileTool` (`search_file`)**:
   - Fast multi-directory & drive crawler searching for games, files, or folders by name across user folders (`Desktop`, `Downloads`, `Documents`, `C:\`, `D:\`, `Program Files`, `Games`, etc.) with optional auto-open in File Explorer.
7. **`WriteFileTool` (`write_file`)**:
   - Directly creates/overwrites files with code or text on disk (e.g. `desktop/demo.html`, `script.py`) creating parent directories automatically.
8. **`ReadFileTool` (`read_file`)**:
   - Reads content of files on disk.
9. **`SearchWebTool` (`search_web`)**:
   - Opens user query in default web browser via Google Search (`webbrowser.open`).
10. **`OpenUrlTool` (`open_url`)**:
   - Opens a direct URL in the default browser.
11. **`GetSystemInfoTool` (`get_system_info`)**:
   - Retrieves real-time CPU % (physical/logical cores), RAM total/used/free/percentage, Disk total/used/free/percentage, and Battery statistics via `psutil`.
12. **`TakeScreenshotTool` (`take_screenshot`)**:
   - Takes screen capture via `pyautogui`, timestamps filename, saves to `screenshots/`, and returns absolute path.

#### `tools/tool_registry.py`
- **Class `ToolRegistry`**:
  - `register_tool(tool: BaseTool)`
  - `get_tool(name: str) -> Optional[BaseTool]`
  - `get_tool_schemas() -> List[dict]`
  - `execute_tool(name: str, **kwargs) -> Any`: Dispatches execution with full error boundary handling.
  - `tool_registry`: Default singleton pre-populated with all 9 tools.

---

### 4.4. User Interface (`interfaces/terminal.py`)

- **Class `TerminalInterface`**:
  - Rich-formatted terminal prompt with color highlighting.
  - Displays `You > ` prompt and streams `SERA > ` responses.
  - Built-in Slash Commands:
    - `/help` — Lists commands.
    - `/voice` — Toggles spoken voice output mode (ON/OFF).
    - `/mic` — Interactive microphone recording and speech-to-text input.
    - `/new` — Starts a new conversation session.
    - `/history` — Renders formatted markdown conversation history of current session.
    - `/clear` — Clears terminal window.
    - `/exit` — Graceful shutdown.

---

### 4.5. Voice Layer (`voice/`)

#### `voice/tts.py`
- **Function `clean_text_for_speech(text: str) -> str`**:
  - Strips markdown formatting (headers, bold, italics, code blocks, URLs, bullets) so synthesized speech sounds natural.
- **Class `TextToSpeech`**:
  - Leverages Microsoft Edge Neural TTS (`edge-tts`) with zero API key requirement.
  - Default neural voice: `en-US-AriaNeural`.
  - Asynchronously synthesizes audio and plays back through system default output via `sounddevice` and `soundfile`.
  - Methods: `speak(text, blocking=True)`, `speak_async(text)`.

#### `voice/stt.py`
- **Class `SpeechToText`**:
  - Records 16kHz mono WAV audio from microphone via `sounddevice`.
  - Supports continuous block recording until user stop event (`record_until_stopped`).
  - Sends audio directly to Groq's high-speed Whisper model (`whisper-large-v3-turbo`) for instant, highly accurate transcription.
  - Methods: `record_audio(duration)`, `record_until_stopped(stop_event)`, `transcribe(audio_bytes)`.

#### `voice/wake_word.py`
- **Class `WakeWordListener`**:
  - Background audio energy monitor and wake phrase verifier ("Hey Sera", "Sera", "Jarvis").
  - Non-blocking background thread with callback dispatching (`start(on_wake)`, `stop()`).

---

### 4.6. Coding Assistant Layer (`tools/coding_tools.py`)

#### `tools/coding_tools.py`
- **Class `ExecuteCodeTool` (`execute_code`)**:
  - Sandboxed subprocess execution for Python (`sys.executable`), Node.js (`node`), PowerShell, or CMD.
  - Automatically captures `stdout`, `stderr`, and `exit_code` with configurable timeout safety (default 15s).
- **Class `EditFileTool` (`edit_file`)**:
  - Precision targeted file content editor that locates a specific `target_text` block and replaces it with `replacement_text`.

#### Autonomous Self-Debugging Engine:
- SERA captures runtime tracebacks and error messages from `execute_code`.
- Autonomously analyzes the failure, applies the fix to disk using `edit_file` or `write_file`, and re-executes `execute_code` until the test passes.

---

### 4.7. Modular Skills Plugin Layer (`skills/`)

#### `skills/base_skill.py`
- **Class `BaseSkill(ABC)`**:
  - Base class providing `get_tools() -> List[BaseTool]`, `name`, and `description`.

#### `skills/skill_manager.py`
- **Class `SkillManager`**:
  - Dynamically scans `skills/*.py` at startup, instantiates skill classes, and registers their tools directly into `tool_registry`.
  - Methods: `discover_and_load_skills()`, `get_loaded_skills_summary()`.

#### `skills/notes_skill.py`
- **Class `NotesSkill(BaseSkill)`**:
  - Tools: `add_note(title, content)`, `list_notes()`.
  - Stores personal notes and reminders in `data/notes.json`.

#### `skills/dev_workflow_skill.py`
- **Class `DevWorkflowSkill(BaseSkill)`**:
  - Tools:
    - `scaffold_project(project_type, destination_folder, name)`: Creates starter templates for `react_component`, `express_api`, `fastapi_api`, `html_tailwind`, `python_cli`.
    - `get_dev_preferences()`: Retrieves Arslan's full-stack preferences (React, Node, Express, Mongo, Python, Tailwind) from `data/developer_preferences.json`.

#### `skills/crm_skill.py`
- **Class `CRMSkill(BaseSkill)`**:
  - Tools:
    - `create_lead(name, email, phone, company, deal_value, status, notes)`: Adds new client lead to `data/leads.json`.
    - `list_leads(filter_status)`: Filters and lists active business opportunities.
    - `update_lead_status(lead_identifier, new_status, new_notes)`: Updates lead pipeline stage and notes.

---

## 5. End-to-End Execution Flow (Data & Control Flow)

```
[ User Input in Terminal ]
            │
            ▼
[ TerminalInterface ] ───> Checks for slash commands (/new, /history, etc.)
            │
            ▼
[ Orchestrator.handle_user_message() ]
            │
            ├─► 1. Save user turn to SQLite (MemoryStore.save_message)
            ├─► 2. Load context history (MemoryStore.get_conversation_history)
            ├─► 3. Retrieve tool schemas (ToolRegistry.get_tool_schemas)
            │
            ▼
   [ GroqProvider.generate_response(stream=False) ]
            │
            ├──► Case A: Text Only Response
            │       │
            │       └─► Stream tokens directly to TerminalInterface ──► [ Output to User ]
            │
            └──► Case B: LLM Emits Tool Call(s)
                    │
                    ├─► 1. Save assistant tool call in SQLite
                    ├─► 2. ToolRegistry.execute_tool(tool_name, **args)
                    │        └── (e.g. GetSystemInfoTool, OpenAppTool, ScaffoldProjectTool, CreateLeadTool, etc.)
                    ├─► 3. Save tool output with role="tool" in SQLite
                    ├─► 4. Re-query LLM with tool output included
                    │
                    └─► 5. Stream final natural language answer ─────► [ Output to User ]
```

---

## 6. History of Changes & Recent Refactoring

1. **Phase 1 Fixes & Stabilization:**
   - Fixed broken relative imports in `core/orchestrator.py` (`from ..models...` changed to top-level absolute imports).
   - Fixed SQLite timestamp collation by using `ORDER BY id DESC` in `memory_store.py` for deterministic chronological message retrieval.
   - Upgraded Groq model configuration in `core/config.py` and `.env` to supported modern models (`openai/gpt-oss-120b` / `qwen/qwen3.8-27b`).
   - Configured `sys.stdout.reconfigure(encoding='utf-8')` in `main.py` to prevent Windows `cp1252` encoding errors.
2. **Complete Codebase Rebranding:**
   - Completely renamed all references from `JARVIS-Lite` / `SIRO` to **`SERA`** across prompt files, log files (`logs/sera.log`), database defaults (`data/sera.db`), UI headers, and test cases.
3. **Phase 2 Implementation:**
   - Created clean `tools/` package with `BaseTool` abstraction and automatic schema generation.
   - Built and integrated all 10 PC control tools (`OpenAppTool`, `CloseAppTool`, `OpenFolderTool`, `OpenFileTool`, `ListFilesTool`, `SearchFileTool`, `SearchWebTool`, `OpenUrlTool`, `GetSystemInfoTool`, `TakeScreenshotTool`).
   - Implemented multi-step agentic execution loop in `Orchestrator` allowing chained tool executions (search -> find -> open).
   - Built comprehensive test suite (`tests/test_phase2.py`).
4. **Phase 3 Voice Layer Implementation:**
   - Created `voice/` package with `TextToSpeech` (`edge-tts` Microsoft neural voice) and `SpeechToText` (Groq `whisper-large-v3-turbo`).
   - Built `clean_text_for_speech` regex engine removing markdown symbols before audio synthesis.
   - Integrated `/voice` (TTS toggle) and `/mic` (speech-to-text input) commands in `interfaces/terminal.py`.
   - Built automated test suite (`tests/test_phase3.py`).
5. **Phase 4 Coding Assistant Module:**
   - Created `tools/coding_tools.py` with `ExecuteCodeTool` (sandboxed subprocess for Python, JS, PowerShell) and `EditFileTool` (targeted code block replacements).
   - Added direct file manipulation tools `WriteFileTool` and `ReadFileTool`.
   - Programmed autonomous self-debugging loop in system prompt and orchestrator.
   - Built automated test suite (`tests/test_phase4.py`).
6. **Phase 5 Wake Word & Dynamic Skills:**
   - Built `WakeWordListener` (`voice/wake_word.py`) for hands-free "Hey Sera" voice activation in background thread.
   - Built dynamic plugin engine `SkillManager` (`skills/skill_manager.py`) with built-in `NotesSkill` (`skills/notes_skill.py`).
   - Added `/wake` and `/skills` interactive terminal commands.
   - Built automated test suite (`tests/test_phase5.py`).
7. **Personalized Identity & Developer Workflow Integration:**
   - Injected Arslan Ali Mansoori's background, education (B.Tech, Sushila Devi Bansal College of Engineering), AI Engineering internship (Shippoz), and projects (DeepGuard, Sustainability Development System, AeroInspect AI) into `data/user_profile.json` and system prompts.
   - Created `data/developer_preferences.json` and `skills/dev_workflow_skill.py` (`scaffold_project`, `get_dev_preferences`) enforcing React.js, Node.js, Express, MongoDB, Python, and Tailwind CSS code standards.
8. **Robustness, Safety Bounds & CRM Business Skill Expansion:**
   - Added `MAX_DEBUG_ITERATIONS = 4` safety cap in `Orchestrator` with post-mortem logging to `logs/sera.log` and user guidance fallback.
   - Built multi-model fallback chain in `GroqProvider` (`core/llm_client.py`).
   - Implemented system-critical process blacklist protection in `CloseAppTool`.
   - Added search timeout cutoff (8s) in `SearchFileTool`, and added `DeleteFileTool` and `MoveFileTool`.
   - Created `CRMSkill` (`skills/crm_skill.py`) and skill-level permission toggle engine (`/skills enable/disable <name>`).
   - Added end-to-end integration test suite (`tests/test_e2e_integration.py`).
9. **Full-Stack Glassmorphic Web & Desktop Frontend:**
   - Built FastAPI backend server in `interfaces/web_server.py` exposing chat, history, system metrics, CRM leads, code scaffolding, and voice endpoints.
   - Built responsive, single-page Glassmorphic Cyberpunk Dark Dashboard in `interfaces/web/index.html` featuring Chat Hub, CRM Pipeline Kanban, Code Scaffolder, Live Hardware Gauges, Skills Manager, and Developer Profile.
   - Added `--ui` / `-w` command-line flags and `/ui` in-app terminal command to launch the browser UI seamlessly.
10. **Daily Brief Orientation Skill:**
   - Created `skills/daily_brief_skill.py` (`GetDailyBriefTool`, `DailyBriefSkill`) synthesizing tasks, notes, client deliverables/payments (with graceful degradation if absent), recent coding context, and hardware snapshots into a fluent, TTS-ready summary.
   - Added `/brief` terminal command for instant briefing, auto-creation of `data/state.json` with once-per-day gating logic, and `AUTO_BRIEF_ON_START` configuration flag.
11. **RGPV Exam-Prep Study Session Skill:**
   - Created `skills/study_session_skill.py` (`StartStudyTool`, `EndStudyTool`, `QuizMeTool`, `GetStudyStatsTool`, `StudySessionSkill`) storing study logs in `data/study_sessions.json`.
   - Built single active session concurrency guard, automatic duration computation, recall quiz material retrieval without hallucination, and lookback time aggregation by subject.
   - Added note subject tagging and automatic session active-subject tagging in `skills/notes_skill.py`.
12. **Job / Internship Application Tracker Skill:**
   - Created `skills/job_tracker_skill.py` (`LogApplicationTool`, `UpdateApplicationStageTool`, `ListPendingFollowupsTool`, `GetApplicationStatsTool`, `JobTrackerSkill`) storing applications in `data/job_applications.json` using atomic writes.
   - Built difflib fuzzy company matching, note appending, 14+ day old application follow-up auto-suggestions, and funnel statistics.
   - Seamlessly integrated pending follow-ups into `skills/daily_brief_skill.py` for orientation briefings.
13. **Global Hotkey Clipboard Capture & Auto-Filing Skill:**
   - Created `core/clipboard_listener.py` (`ClipboardCaptureListener`) running a background hotkey listener (`Ctrl+Shift+S`) with 2-second debounce protection and non-blocking daemon thread callback.
   - Created `skills/clipboard_capture_skill.py` (`ProcessClipboardCaptureTool`, `AddLinkToReadLaterTool`, `ClipboardCaptureSkill`) providing heuristic pre-classification (code, task, link, note), automatic filing into `data/notes.json` or `data/read_later.json`, and persistent audit logging in `data/captures.json`.
   - Integrated `/capture` toggle command into `interfaces/terminal.py` with instant Rich toast notifications and updated system prompt with synthetic `[CLIPBOARD CAPTURE]` handling.
14. **Developer Studio Command Center (Daylight Edition Redesign):**
   - Transformed UI from dark cyberpunk into a bright, dimensional developer ops console (`interfaces/web/index.html`, `app.css`, `app.js`, `DESIGN.md`).
   - Grounded design tokens: Porcelain Slate base (`#F8FAFC`), Studio White elevated cards (`#FFFFFF`), Electric Sapphire primary action (`#3B82F6`), Emerald Viridian live indicator (`#059669`), and multi-stop ambient physical shadows (`--shadow-sm`, `--shadow-md`, `--shadow-lg`).
   - Integrated `Plus Jakarta Sans` for clean, professional display headings and UI typography; `JetBrains Mono` strictly for data, code, IDs, and hardware telemetry.
   - **Signature 3D Moment**: Instrument-grade physically-lit **3D Radial Telemetry Dials** with specular rims, recessed inner tracks, embossed hubs, and dynamic stroke-dash arcs.
   - **Critical Bug Fixes Resolved**:
     - *Hardware Gauges `--%` Bug*: Fully data-bound CPU, RAM, and Disk percentage values (`#dial-cpu-val`, `#dial-ram-val`, `#dial-disk-val`) and stroke offsets to live `/api/system-info` polled every 3.5s.
     - *CRM Duplicate Rows*: Pruned duplicate test leads from `data/leads.json` and implemented client-side deduplication by unique contact & company.
     - *Connection Status*: High-contrast `● LIVE` emerald badge and `○ OFFLINE` amber badge.
15. **UX & Interaction Rebuild (AI State Orb & Affordance Engine):**
   - Transformed interface into an active, responsive command center with rich feedback on every user and AI action.
   - **Functional 3D Hero Element (AI State Orb)**: Docked mini orb in top header and hero orb in Chat Hub dynamically reflecting real agentic state machine (`idle`, `listening`, `thinking` with live tool execution labels, and `speaking`), wired to real `/ws/chat` socket events and `orchestrator.py`.
   - **Unified Toast System**: Built accessible, animated notification manager with role status and auto-dismissal for all user actions.
   - **Command Palette (`Ctrl+K` / `Cmd+K`)**: Keyboard-driven command center for instant navigation, study triggers, and mode toggling.
   - **Interaction Upgrades Across Panels**:
     - *In-Place Study Session Transition*: Selecting subject chips provides tactile pressed states; starting immediately renders a live running stopwatch in-place.
     - *Interactive CRM Accordions*: Clicking leads expands inline details; stage can be updated directly from the Console preview via dropdown.
     - *Structured Daily Brief*: Organized into scannable action/ambient blocks with a busy-state spinner button.
     - *Hardware Telemetry Sparklines & Thresholds*: Hover sparkline showing 60s trend, dynamic warning/critical dial color shifts.
     - *Connection Status Popover*: Detailed status popover on connection badge click.
     - *WebSocket Protocol Engine*: Installed and pinned `websockets` dependency to resolve Uvicorn `Unsupported upgrade request` warnings during streaming chat.
16. **React.js Frontend Architecture (`frontend/` + Vite Bundle):**
   - Completely switched web interface to modern, modular **React.js 18** with Tailwind CSS and Vite.
   - Project location: `frontend/` containing idiomatic React components:
     - `AppContext.jsx`: Central state management for WebSocket connection, token streaming, telemetry polling, toast queue, and active modes.
     - `TopBar.jsx`: Mini AI State Orb, 60s sparkline telemetry popovers, connection diagnostics popover, mode toggles (`Hey Sera`, `Voice`, `Capture`), and new session launcher.
     - `NavRail.jsx`: Navigation rail with active route states and urgent follow-up attention badges.
     - `AiStateOrb.jsx`: Reusable functional 3D orb reflecting `idle`, `listening`, `thinking` (with live tool name label), and `speaking`.
     - `CommandPalette.jsx`: Global `Ctrl+K` keyboard overlay with fuzzy command search.
     - `ConsoleView.jsx`: Structured Daily Brief, in-place Study Session stopwatch, 3D Radial Gauges with threshold warnings, and CRM accordion cards.
     - `ChatHubView.jsx`: Hero AI State Orb, token streaming bubbles, live tool indicator, and voice recording.
     - `PipelineView.jsx`: 5-stage Job Application Funnel and 5-stage Client CRM Kanban.
     - `StudyLabView.jsx`: RGPV Exam study sessions with live timer and 7-day revision breakdown.
     - `DevSystemView.jsx`: Code scaffolder, dynamic skill manager, and clipboard capture audit logs.
   - Vite builds directly to `interfaces/web/` so running `python main.py --ui` serves the React production build out-of-the-box on `http://127.0.0.1:8000`.
   - Developer mode enabled with `npm run dev` in `frontend/` with hot module replacement (HMR) proxying to FastAPI.
   - Full test suite verified at **77/77 passing automated tests**.
17. **Phase 7: System Insights — Hardware, OS & Software Diagnostics:**
   - **Goal**: Full-spectrum, read-only PC hardware telemetry, OS identification, application inventory, game detection, startup items, and running process diagnostics.
   - **Components Implemented**:
     1. **Backend Skill (`skills/system_insights_skill.py`)**:
        - `get_pc_overview`, `list_installed_apps`, `list_installed_games`, `list_startup_programs`, `list_running_processes`, `get_network_info`, `get_battery_and_power_info`, `get_user_account_info`.
     2. **FastAPI Endpoints (`interfaces/web_server.py`)**:
        - New `/api/system/*` routes strictly bound to `127.0.0.1`.
     3. **React Frontend View (`frontend/src/components/views/SystemInsightsView.jsx`)**:
        - New left-rail navigation item "System Insights", in-page sub-tabs, interactive search, and live polling.
     4. **Automated Verification**:
        - 9 new unit/integration tests in `tests/test_system_insights.py`.
        - Full test suite verified at **86/86 passing automated tests**.

---

## 7. How to Run, Test, and Extend

### Run the Application
- **Modern Web Dashboard**:
```powershell
.\venv\Scripts\python.exe main.py --ui
```
- **Terminal CLI Mode**:
```powershell
.\venv\Scripts\python.exe main.py
```

### Run All Automated Tests (77 Tests)
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### How to Add a New Tool in 3 Steps:
1. Create a class inheriting from `BaseTool` in `tools/`:
   ```python
   from tools.base_tool import BaseTool

   class MyCustomTool(BaseTool):
       name = "my_tool"
       description = "Does something custom."
       parameters = {
           "type": "object",
           "properties": {
               "param1": {"type": "string", "description": "Parameter description"}
           },
           "required": ["param1"]
       }

       def execute(self, param1: str):
           return {"status": "success", "data": f"Processed {param1}"}
   ```
2. Register it in `tools/tool_registry.py`:
   ```python
   registry.register_tool(MyCustomTool())
   ```
3. SERA's LLM will automatically receive the JSON schema and know when to call it.
