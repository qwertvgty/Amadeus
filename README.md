# LifeOS - Personal AI Agent System

A proactive personal AI assistant with long-term memory, task planning, tool execution, and proactive reminders.

## Quick Start

### Prerequisites

- Python 3.11+
- An LLM API key (OpenAI / Anthropic / DeepSeek)

### Setup

```bash
# Create virtual environment and install
uv venv .venv
source .venv/Scripts/activate  # Windows Git Bash
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python scripts/init_db.py
```

### Run

```bash
# Terminal 1: Start backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Start frontend
streamlit run frontend/app.py
```

### Verify

- Backend health: http://localhost:8000/health
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:8501

## Architecture

See `docs/` for detailed architecture documentation.

## Tech Stack

- **Backend**: Python + FastAPI + Pydantic
- **Agent Orchestration**: LangGraph
- **Storage**: SQLite + Chroma
- **Frontend**: Streamlit
- **Scheduling**: APScheduler
- **Logging**: Loguru
