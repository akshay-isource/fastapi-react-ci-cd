# DevFlow AI — Frontend

React dashboard for the DevFlow AI platform. Includes a CI/CD pipeline dashboard and an **AI Research Assistant** page that connects to the multi-agent backend.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `dashboard` | Stats, pipeline flow, API health, recent activity |
| Research | `research` | AI Research Assistant — runs the multi-agent pipeline |
| Pipeline | `pipeline` | Pipeline management (coming soon) |
| APIs | `apis` | API endpoint testing (`/api/hi`, `/api/echo`) |
| Settings | `settings` | Platform settings (coming soon) |

## AI Research Page

The Research page connects to the `agent-app` backend and provides:

- **Search input** — enter a research topic
- **Agent pipeline visualization** — shows 8 agents with real-time status (running/completed/retry)
- **Quality score** — color-coded badge (green 7+, orange 4-6, red below 4)
- **Final report** — markdown-rendered research output
- **Collapsible panels** — raw research data, analysis, activity log

Communication uses **Server-Sent Events (SSE)** for real-time streaming from the backend.

## Setup

### 1. Install dependencies

```bash
cd frontend
npm install
```

### 2. Configure environment (optional)

Create a `.env` file in the `frontend/` directory:

```env
# Main backend API (for dashboard, APIs page)
REACT_APP_API_BASE_URL=/api

# Agent backend (for Research page)
REACT_APP_RESEARCH_API_URL=http://localhost:8001
```

Defaults work for local development without a `.env` file.

### 3. Run the dev server

```bash
npm start
```

Opens at `http://localhost:3000`.

### 4. Build for production

```bash
npm run build
```

Output goes to `build/` — static files ready to serve via nginx or any static host.

## Running with the Agent Backend

To use the Research page, the agent backend must be running:

```bash
# Terminal 1 — agent backend
cd agent-app
python main.py          # starts on port 8001

# Terminal 2 — frontend
cd frontend
npm start               # starts on port 3000
```

Then open `http://localhost:3000`, click **Research** in the sidebar, enter a topic, and click **Research**.

## Tech Stack

- React 19
- Axios (API calls)
- CSS variables for dark/light theme support
- No external UI libraries — custom components
