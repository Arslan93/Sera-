# SERA — Personal AI Desktop & Coding Companion

> **SERA** (*Synthetically Engineered Responsive Assistant*) is a fast, low-latency, modular personal AI desktop assistant, voice companion, and developer command center built with **Python**, **FastAPI**, **React 18**, **Groq**, **Microsoft Edge Neural TTS**, and **Windows PC Automation**.

---

## 🌟 Key Capabilities

| Domain | Features |
|---|---|
| 🧠 **Agentic Brain** | Powered by Groq `openai/gpt-oss-120b` with autonomous multi-tier fallback cascade (`llama-3.3-70b-versatile`, `mixtral-8x7b-32768`), tool-calling loop, and self-debugging engine. |
| ⚛️ **Modern React Frontend** | Full React 18 SPA (`frontend/`) with Tailwind CSS, 3D radial hardware dials, functional **AI State Orb**, `Ctrl+K` command palette, and real-time WebSocket streaming. |
| 🎙️ **Voice & Ambient Layer** | Hands-free background "Hey Sera" wake word detector, Groq Whisper Speech-To-Text (`whisper-large-v3-turbo`), and Microsoft Neural TTS (`edge-tts`). |
| 💻 **Developer Studio** | Sandboxed subprocess code runner (`execute_code`), targeted file editor (`edit_file`), instant multi-framework code scaffolder (React, Express, FastAPI, HTML/Tailwind). |
| 🧩 **Extensible Skills** | Dynamic plugin subsystem (`skills/`) with Daily Orientation Brief, RGPV Exam Study Sessions, Job & Internship Tracker, Client CRM Kanban, and Global Clipboard Hotkey (`Ctrl+Shift+S`). |
| 💾 **Memory & Local Storage** | Persistent SQLite conversation history (`data/sera.db`) + crash-resilient atomic JSON stores (`data/*.json`). |

---

## 📐 Architecture

For a comprehensive technical deep-dive, component diagrams, and sequence flows, refer to [`ARCHITECTURE.md`](file:///c:/Users/HP/Desktop/Jarvis/ARCHITECTURE.md).

```text
[React 18 SPA / Vite] <──WebSocket & REST──> [FastAPI Server (:8000)]
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
         [Orchestrator Brain Loop]                                     [Ambient Daemon Listeners]
         ├── Groq LLM (gpt-oss-120b)                                   ├── Wake Word ("Hey Sera")
         ├── Fallback Cascade (llama-3.3-70b)                          ├── Hotkey (Ctrl+Shift+S)
         ├── Autonomous Self-Debugging                                 └── Voice Engine (TTS/STT)
         ├── Tool Registry (10 Desktop Tools)
         └── Skill Manager (Daily Brief, Study, Job Tracker, CRM)
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js v20+** & **npm** (for React development)
- **Windows OS**

### 2. Environment Setup
Activate the virtual environment and verify your Groq API credentials:
```powershell
.\venv\Scripts\activate
```
Ensure your `.env` contains:
```ini
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

### 3. Launching SERA

#### Option A: Run Backend Server via npm
```powershell
npm run server
```
*(Runs the FastAPI backend and serves the React dashboard at `http://127.0.0.1:8000`)*

#### Option B: Full-Stack Dev Mode (Backend + React Vite concurrently)
```powershell
npm start
```
*(Runs both the FastAPI backend and Vite hot-reloading dev server concurrently in a single terminal)*

#### Option C: React UI Only (Hot Reloading)
```powershell
npm run dev
```
*(Runs Vite on `http://localhost:3000` with instant HMR)*

#### Option D: Terminal CLI Chat Mode
```powershell
.\venv\Scripts\python.exe main.py
```

---

## 🧪 Automated Testing

SERA includes a comprehensive test suite of **77 automated unit and integration tests**:

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

Tests cover:
- Agentic tool calling and multi-turn loops
- Self-debugging error recovery & loop guardrails
- SQLite conversation memory persistence
- Voice synthesis and Whisper transcription
- Desktop automation (process control, file search, screenshots)
- Dynamic skill plugin lifecycle & discovery
- Daily Brief, Study Session, Job Tracker, and CRM engines
- Global Hotkey clipboard capture and debounce logic
- FastAPI REST endpoints, WebSocket streaming, and static asset delivery

---

## ⌨️ In-App Commands & Shortcuts

| Trigger | Action |
|---|---|
| `Ctrl+K` | Open global **Command Palette** modal |
| `Ctrl+Shift+S` | Global Hotkey to capture clipboard content and auto-file via LLM |
| `/brief` | Trigger Daily Orientation Briefing |
| `/capture` | Toggle clipboard capture listener |
| `/voice` | Toggle spoken TTS audio responses |
| `/wake` | Toggle hands-free "Hey Sera" wake word detector |
| `/mic` | Trigger microphone audio transcription |
| `/skills` | Inspect and toggle dynamic skill plugins |
| `/new` | Start a clean conversation session |
| `/history` | View conversation turns in current session |
| `/ui` | Open the React Web Dashboard |
| `/exit` | Gracefully shut down SERA |

---

## 📂 Repository Structure

```text
Jarvis/
├── main.py                    # Unified entrypoint CLI / UI launcher
├── requirements.txt           # Python backend dependencies
├── ARCHITECTURE.md            # System architecture & sequence diagrams
├── context.md                 # Complete project context & developer history
├── core/
│   ├── orchestrator.py        # Agentic loop, tool calling, model fallback
│   ├── clipboard_listener.py  # Global hotkey (Ctrl+Shift+S) daemon
│   └── models.py              # Pydantic schemas & state models
├── frontend/                  # React.js 18 project source (Vite + Tailwind)
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx            # Layout manager
│       ├── context/           # Central AppContext state & WebSockets
│       └── components/        # Reusable UI widgets & 5 modular views
├── interfaces/
│   ├── web_server.py          # FastAPI REST & WebSocket streaming server
│   ├── terminal.py            # Rich color terminal CLI interface
│   └── web/                   # Compiled production React build
├── memory/                    # SQLite database & session management
├── skills/                    # Modular skill plugins (Daily Brief, Study, Jobs, CRM)
├── tools/                     # 10 core PC automation and coding tools
├── voice/                     # Edge-TTS, Whisper STT, and PyAudio wake-word
├── data/                      # Persistent SQLite DB and atomic JSON stores
└── tests/                     # 77 automated pytest integration suites
```

---

## 👤 Developer

Built with passion by **Arslan Ali Mansoori**  
*B.Tech Computer Science & Engineering*  
Sushila Devi Bansal College of Engineering, Indore
