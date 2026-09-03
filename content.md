# SERA AI — Project Architecture, Content & Context Index

> **SERA (Synthetically Engineered Responsive Assistant)**  
> Personal AI Desktop Assistant, Developer Command Center & Voice Companion built for Arslan Ali Mansoori.

---

## 📑 Core Documentation Index

This repository provides three dedicated, synchronized documentation guides:

1. **[`ARCHITECTURE.md`](file:///c:/Users/HP/Desktop/Jarvis/ARCHITECTURE.md)**:
   - Complete technical blueprint & architecture diagrams (Mermaid)
   - Component layers: React 18 SPA (6 Workbench Views), FastAPI Gateway, Groq Agentic Orchestrator, Extensible Skill Plugins (7 Skills), Persistence, and Ambient Listeners
   - Finite state machine for the functional 3D AI State Orb
   - Read-only diagnostic privacy scope and reliability guardrails

2. **[`context.md`](file:///c:/Users/HP/Desktop/Jarvis/context.md)**:
   - Full chronological development log across all 7 phases
   - Detailed specifications for all 10 desktop automation tools and 7 dynamic skills
   - Developer preferences, RGPV exam syllabus alignment, and CRM structure
   - Comprehensive test suite inventory (86 automated unit and integration tests)

3. **[`README.md`](file:///c:/Users/HP/Desktop/Jarvis/README.md)**:
   - User-facing quickstart guide
   - Production launch (`npm run server`), development mode (`npm run dev`), fullstack mode (`npm start`)
   - CLI commands, System Insights panel, and global hotkey shortcuts (`Ctrl+Shift+S`, `Ctrl+K`)

---

## 🏗️ High-Level System Structure

```text
Jarvis/
├── main.py                     # Primary launcher (CLI or Web UI)
├── requirements.txt            # Python dependencies (fastapi, uvicorn, websockets, groq, etc.)
├── ARCHITECTURE.md             # Complete system architecture & sequence flows
├── context.md                  # Comprehensive AI context & technical reference
├── content.md                  # Content index & quick navigation guide
├── README.md                   # User manual & quickstart instructions
├── core/
│   ├── orchestrator.py         # Multi-turn tool calling & self-debugging loop
│   ├── clipboard_listener.py   # Global background hotkey (Ctrl+Shift+S) daemon
│   └── llm_client.py          # Groq provider with multi-tier model fallback
├── frontend/                   # React 18 SPA Source (Vite + Tailwind CSS)
│   ├── src/App.jsx             # Main workbench layout (Console, Chat, Pipeline, Study, Dev, Insights)
│   ├── src/context/            # WebSocket streaming & AI state engine
│   └── src/components/         # 3D Dials, AI State Orb, Command Palette, 6 Views
├── interfaces/
│   ├── web_server.py           # FastAPI server with WebSocket streaming (/ws/chat) & System Insights APIs
│   ├── terminal.py             # Rich interactive CLI
│   └── web/                    # Compiled production React application
├── skills/                     # 7 modular skills (System Insights, Daily Brief, Study, Job Tracker, CRM, Notes, Clipboard)
├── tools/                      # 10 core PC control, coding, and file management tools
├── voice/                      # Microsoft Edge Neural TTS & Groq Whisper STT
├── memory/                     # SQLite database manager & message history
├── data/                       # Local SQLite DB (sera.db) and atomic JSON stores
└── tests/                      # 86 automated unit and integration tests (100% passing)
```

---

## 🚀 Quick Commands
```powershell
# 1. Run Backend Server via npm (FastAPI + React Dashboard)
npm run server

# 2. Run Full-Stack Mode (Backend + React Vite concurrently)
npm start

# 3. Run React Hot-Reloading Dev Server Only
npm run dev

# 4. Run Terminal Interactive Mode
.\venv\Scripts\python.exe main.py

# 5. Run Full Test Suite (86 Tests)
npm test
```
