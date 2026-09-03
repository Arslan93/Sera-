# SERA AI — Project Architecture, Content & Context Index

> **SERA (Synthetically Engineered Responsive Assistant)**  
> Personal AI Desktop Assistant, Developer Command Center & Voice Companion built for Arslan Ali Mansoori.

---

## 📑 Core Documentation Index

This repository provides three dedicated, synchronized documentation guides:

1. **[`ARCHITECTURE.md`](file:///c:/Users/HP/Desktop/Jarvis/ARCHITECTURE.md)**:
   - Complete technical blueprint & architecture diagrams (Mermaid)
   - Component layers: React 18 SPA, FastAPI Gateway, Groq Agentic Orchestrator, Extensible Skill Plugins, Persistence, and Ambient Listeners
   - Finite state machine for the functional 3D AI State Orb
   - Security, process sandboxing, and reliability guardrails

2. **[`context.md`](file:///c:/Users/HP/Desktop/Jarvis/context.md)**:
   - Full chronological development log across all 6 phases
   - Detailed specifications for all 10 desktop automation tools and 6 dynamic skills
   - Developer preferences, RGPV exam syllabus alignment, and CRM structure
   - Comprehensive test suite inventory (77 automated unit and integration tests)

3. **[`README.md`](file:///c:/Users/HP/Desktop/Jarvis/README.md)**:
   - User-facing quickstart guide
   - Production launch (`main.py --ui`) and React development mode (`npm run dev`)
   - CLI commands and global hotkey shortcuts (`Ctrl+Shift+S`, `Ctrl+K`)

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
│   ├── src/App.jsx             # Main workbench layout
│   ├── src/context/            # WebSocket streaming & AI state engine
│   └── src/components/         # 3D Dials, AI State Orb, Command Palette, 5 Views
├── interfaces/
│   ├── web_server.py           # FastAPI server with WebSocket streaming (/ws/chat)
│   ├── terminal.py             # Rich interactive CLI
│   └── web/                    # Compiled production React application
├── skills/                     # Modular skills (Daily Brief, Study Session, Job Tracker, CRM, Notes)
├── tools/                      # 10 core PC control, coding, and file management tools
├── voice/                      # Microsoft Edge Neural TTS & Groq Whisper STT
├── memory/                     # SQLite database manager & message history
├── data/                       # Local SQLite DB (sera.db) and atomic JSON stores
└── tests/                      # 77 automated unit and integration tests (100% passing)
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

# 5. Run Full Test Suite (77 Tests)
npm test
```
