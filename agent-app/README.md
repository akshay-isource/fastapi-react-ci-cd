# AI Research Team — Multi-Agent Backend

A multi-agent research assistant built with **LangGraph** and **FastAPI**. Three specialized AI researchers work in parallel, their output is analyzed, quality-checked, and polished into a final report.

## Architecture

```
              +-> News Researcher ------+
START -> Dispatcher -> Academic Researcher -> Merger -> Analyst -> Quality Checker -> Writer -> END
              +-> Stats Researcher -----+                              |
              ^                                                        |
              +----------------------- (retry if score < 7) ----------+
```

**Agents:**

| Agent | Role | Tools | LLM |
|-------|------|-------|-----|
| Dispatcher | Fan-out routing (no LLM) | None | None |
| News Researcher | Recent news and trends | Web Search | Yes |
| Academic Researcher | Expert opinions and studies | Web Search | Yes |
| Stats Researcher | Numbers, metrics, data | Web Search | Yes |
| Merger | Combines research (no LLM) | None | None |
| Analyst | Identifies patterns and gaps | None | Yes |
| Quality Checker | Scores analysis, targeted feedback | None | Yes (structured output) |
| Writer | Polished markdown report | None | Yes |

**Key Patterns:**
- Parallel execution (fan-out/fan-in)
- Conditional edges (quality gate with retry loop)
- Custom reducer (`dedupe_by_source`) to prevent duplicate data on retry
- Targeted per-researcher feedback on retry
- Pydantic structured output for quality checker
- Cost optimization with prompt limits and `max_tokens`

## Project Structure

```
agent-app/
  main.py                 # FastAPI server (port 8001)
  llm_provider.py         # Multi-provider LLM factory
  agents/
    parallel_researchers.py  # 3 specialized researchers
    merger.py                # Fan-in combiner (no LLM)
    analyst.py               # Analysis agent
    quality_checker.py       # Quality gate with structured output
    writer.py                # Final report writer
  graph/
    state.py              # ResearchState + custom reducer
    workflow.py           # LangGraph graph definition
  tools/
    search.py             # DuckDuckGo web search tool
```

## Setup

### 1. Create virtual environment

```bash
cd agent-app
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create a `.env` file in the `agent-app/` directory:

```env
# Choose your LLM provider: anthropic, openai, google, sarvam
LLM_PROVIDER=anthropic

# API key for your chosen provider
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GOOGLE_API_KEY=...
# SARVAM_API_KEY=...

# Optional: override the default model
# LLM_MODEL=claude-sonnet-4-20250514
```

### 4. Run the server

```bash
python main.py
```

The server starts at `http://localhost:8001`.

## API Endpoints

### Health Check

```bash
GET /health
```

### Run Research (full response)

```bash
POST /research
Content-Type: application/json

{"query": "Impact of AI on cybersecurity jobs"}
```

### Run Research (streaming via SSE)

```bash
POST /research/stream
Content-Type: application/json

{"query": "Impact of AI on cybersecurity jobs"}
```

Returns Server-Sent Events with real-time agent progress updates.

## Cost

~$0.013 per query (~6k tokens) with Anthropic Claude Sonnet. Optimized via:
- 50-word limits on researcher prompts
- 80-word limit on analyst
- 100-word limit on writer
- `max_tokens` caps on all agents
- Trimmed input data between agents
- Pydantic structured output (no verbose format instructions)
