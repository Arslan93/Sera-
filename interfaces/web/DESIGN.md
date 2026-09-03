# SERA Studio Command Center — Frontend Design System (Daylight Edition)

A bright, dimensional, information-forward developer ops console and personal command center for Arslan Ali Mansoori (B.Tech CSE, AI Engineer).

---

## 1. Visual Philosophy & Rejection of AI Clichés

| Common AI-Generated Cliché | SERA Studio Grounding & Execution |
| :--- | :--- |
| Dark cyberpunk `#000000` / `#0B0B0B` with neon purple/cyan accents | **Porcelain Slate (`#F8FAFC`)** base with elevated **Studio White (`#FFFFFF`)** cards. Bright, daylight-clarity inspired by Linear, Arc Browser, and Notion. |
| Flat frosted glass blur (`backdrop-blur-md` on identical rectangles) | **Layered Physical Depth**: Multi-stop ambient shadows (`shadow-resting`, `shadow-raised`, `shadow-floating`) mimicking real daylight falling on physical surfaces. |
| Tracked-out uppercase labels (`E Y E B R O W S`) everywhere | **Sentence / Title Case** clean neo-grotesque hierarchy with purposeful weight contrast. |
| Monospace typography forced onto every button, heading, and badge | **Dual Typography System**: `Plus Jakarta Sans` for headers and UI text; `JetBrains Mono` strictly reserved for data (code, telemetry, timestamps, IDs). |
| Flat progress lines for hardware status | **Signature 3D Moment**: Instrument-grade physically-lit **3D Radial Telemetry Dials** with specular rims, inner shadows, and live data binding. |

---

## 2. Color & Elevation Tokens (Hex Scale)

```
Substrate & Elevation Surfaces:
  surface-base:      #F8FAFC  (Porcelain Slate — soft daylight background, zero harsh glare)
  surface-card:      #FFFFFF  (Studio Card — elevated card surface with physical depth)
  surface-card-sub:  #F1F5F9  (Recessed Well — input containers, metric tracks, code wells)
  surface-hover:     #EEF2F6  (Subtle interactive hover feedback)

Borders & Dividers:
  border-subtle:     #E2E8F0  (Architectural 1px hairline border)
  border-strong:     #CBD5E1  (Active card borders, focused inputs, selected tabs)

Semantic Accents:
  accent-action:     #3B82F6  (Electric Cobalt — User actions: Send, Save, Start, Active Tab)
  accent-action-hover: #2563EB
  accent-live:       #059669  (Emerald Viridian — Live WebSocket stream, active study timer, speech active)
  accent-alert:      #D97706  (Signal Amber — 14+ day follow-up overdue, high RAM/CPU, deadlines)
  accent-danger:     #E11D48  (Crimson Rose — destructive actions)

Text & Contrast:
  text-primary:      #0F172A  (Slate 900 — high-contrast crisp text, >14:1 contrast ratio)
  text-secondary:    #475569  (Slate 600 — clear secondary metadata, >7:1 contrast ratio)
  text-tertiary:     #94A3B8  (Slate 400 — disabled states, subtle borders, micro hints)

Layered Elevation Shadows:
  shadow-resting:    0 1px 2px rgba(15, 23, 42, 0.04), 0 1px 1px rgba(15, 23, 42, 0.02)
  shadow-raised:     0 4px 12px -2px rgba(15, 23, 42, 0.06), 0 2px 4px -1px rgba(15, 23, 42, 0.04)
  shadow-floating:   0 12px 28px -4px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.03)
```

---

## 3. Typography Hierarchy

- **Display & Section Titles:** `Plus Jakarta Sans`, font-weight `600` / `700`, letter-spacing `-0.02em`.
  - Mode Header: `16px` (font-semibold, tracking-tight)
  - Card & Section Titles: `13.5px` (font-semibold, text-primary)
  - Body & Chat: `13.5px` (leading-relaxed, text-primary)
  - Meta & Captions: `11.5px` (font-medium, text-secondary)
- **Data & Telemetry Face:** `"JetBrains Mono", monospace`
  - Real hardware metrics, CPU/RAM percentages, timestamps, code snippets, file paths, and tool parameters.

---

## 4. The Signature 3D Moment: Physically-Lit Hardware Telemetry Dials

Rather than scattering pseudo-3D effects across every panel, SERA commits to **ONE signature dimensional element**:
- **3D Radial Telemetry Dials (CPU, RAM, Disk, Battery)**:
  - Each dial is built as an instrument-grade circular gauge with a specular top highlight (`radial-gradient(ellipse at 50% 0%, rgba(255,255,255,0.8), transparent)`), a recessed inner track with physical drop-shadow (`inset 0 2px 4px rgba(15,23,42,0.1)`), and an embossed physical center hub.
  - The sweep arc dynamically animates and fills according to real, live telemetry polled every 3.5 seconds from `/api/system-info`.
  - The numeric values are strictly bound to live data (`gauge-cpu-val`, `gauge-ram-val`, `gauge-disk-val`) fixing the previous `--%` bug.

---

## 5. Architecture & Layout Wireframe (Console Home View)

```text
+------------------------------------------------------------------------------------------------------------------------+
| [S] SERA  v2.4 [gpt-oss-120b]  |  (●) 18% CPU  (●) 42% RAM  (●) 98% BAT  |  [● LIVE]  [Hey Sera]  [Voice]  [+ New Session] |
+-------+----------------------------------------------------------------------------------------------------------------+
| NAV   | CONSOLE WORKBENCH                                                                                              |
| ----- |                                                                                                                |
| [⊞]   | +------------------------------------------------------------------------------------------------------------+ |
| Cmd   | | ☀️ DAILY ORIENTATION BRIEF (Arslan's Morning Compass)                                       [Refresh] [Speak]| |
|       | | "Good morning, Arslan. 2 follow-ups due: Google, Shippoz. RAM 42%. Last worked on 'Job Tracker Skill'."     | |
| [💬]  | +------------------------------------------------------------------------------------------------------------+ |
| Chat  |                                                                                                                |
|       | +-----------------------------------------------------+ +----------------------------------------------------+ |
| [☷]   | | 🎓 STUDY SESSION VITALS                             | | ⚙️ 3D HARDWARE VITALS CLUSTER (Instrument Cockpit)  | |
| Pipe  | | [Active Stopwatch or Quick Subject Chips: OS, CN]   | |   [ (CPU 18%) ]    [ (RAM 42%) ]    [ (DISK 35%) ]   | |
|       | | Custom Subject & Goal inputs + [Start Block]        | |   Tactile 3D dials, real-time live data binding    | |
| [🎓]  | +-----------------------------------------------------+ +----------------------------------------------------+ |
| Study |                                                                                                                |
|       | +-----------------------------------------------------+ +----------------------------------------------------+ |
| [⚙]   | | 💼 PENDING JOB FOLLOW-UPS (Urgent Alert Strip)      | | 📈 CLIENT CRM PIPELINE (Active Business Leads)     | |
| Dev   | | [Google — SWE Intern (OVERDUE)]                     | | [Alice Enterprise — $10,000 Won]                   | |
|       | | [Amazon — Cloud Support (in 2 days)]                | | [John Doe — $5,000 New]                            | |
|       | | Link: Open Full Funnel (5 stages)                   | | Link: Open Full Kanban                             | |
|       | +-----------------------------------------------------+ +----------------------------------------------------+ |
+-------+----------------------------------------------------------------------------------------------------------------+
```

---

## 6. Real Backend Data Binding (All Bugs Addressed)
1. **Live Hardware Telemetry**: CPU, RAM, Disk, and Battery are now dynamically bound to `/api/system-info` with no static or `--%` placeholders.
2. **Deduplicated CRM Pipeline**: `data/leads.json` has been pruned of historical test duplicates, displaying unique active client opportunities.
3. **High-Contrast Connection Indicator**: Clear `● LIVE` emerald badge when WebSocket is active; amber `○ OFFLINE` when disconnected.

---

## 7. Interaction Patterns & AI State Orb Architecture

### 7.1 The AI State Orb (Functional 3D Hero Moment)
Rather than purely decorative 3D elements, SERA commits its dimensional treatment to **functional state indication** reflecting the live agentic activity of `core/orchestrator.py` via WebSocket events.

#### State Machine Matrix
| State | Visual Treatment | Trigger Event | Accessible Live Announcement |
| :--- | :--- | :--- | :--- |
| **`idle`** | Calm ethereal sapphire orb (`#3B82F6` gradient with specular lens flare), gentle 4s breathing pulse | WebSocket connected, no active inference | `"SERA is idle and ready"` |
| **`listening`** | Pulsing emerald/teal glow (`#10B981` radial gradient), 1.2s respiratory pulse | Microphone recording active via `/api/voice/listen` | `"SERA is listening for speech"` |
| **`thinking` / `tool_call`** | Active violet refractive sheen (`#8B5CF6`), 1.8s rotational orbital glow + live crossfading label: `"Coordinating tool: <tool_name>"` | `orchestrator.py` agentic step executing a tool call | `"SERA state: thinking - calling <tool_name>"` |
| **`speaking`** | Resonant amber/gold frequency pulse (`#F59E0B`), 0.9s alternating scale | TTS audio generation & speech playback active | `"SERA is speaking response"` |

### 7.2 Global Interaction & Affordance Patterns
1. **Unified Toast System**:
   - Fixed at bottom-right viewport with `role="status"` and `aria-live="polite"`.
   - Distinct color-coded left borders (`success` emerald, `info` blue, `warning` amber, `error` rose).
   - Auto-dismisses after 3.5s or on manual dismissal.
2. **Command Palette (`Ctrl+K` / `Cmd+K`)**:
   - Power-user modal overlay accessible from anywhere via keyboard or top bar.
   - Live query filtering, up/down arrow navigation, Enter to execute, Esc to dismiss.
   - Quick navigation to all views, study session triggers, and mode toggles.
3. **In-Place Study Session Transition**:
   - Subject chips (OS, Networks, DBMS, TOC, DL) provide immediate tactile pressed feedback.
   - Clicking "Start" transitions the Console card in-place into an active running timer (`HH:MM:SS`) with note logging and "End Session", eliminating redundant UI while preserving morning orientation context.
4. **Interactive CRM Card Accordion**:
   - Cards expand inline with smooth CSS max-height transitions to reveal notes, emails, and phone numbers.
   - Stage dropdown enables 1-click status transitions directly from the Console preview, immediately calling `POST /api/leads/status` with toast confirmation.
5. **Hardware Threshold Alarms & Sparklines**:
   - Hovering over CPU/RAM chips displays an interactive mini-sparkline showing a 60-second rolling trend.
   - Dials dynamically transition into `dial-warning` (amber, >70%) and `dial-critical` (pulsing crimson, >85%) for ambient hardware health awareness.

