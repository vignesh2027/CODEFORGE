# Configuration Reference

All configuration is via `.env`. Copy `.env.example` and fill in your keys.

## Required Keys

| Variable | Where to get it | Purpose |
|----------|----------------|---------|
| `GROQ_API_KEY` | console.groq.com | LLM inference (Llama 3.3 70B) |
| `TAVILY_API_KEY` | app.tavily.com | Web search in Coder agent |

## Optional: LangSmith Tracing

| Variable | Value | Purpose |
|----------|-------|---------|
| `LANGSMITH_API_KEY` | smith.langchain.com → Settings → API Keys → Personal Token (`lsv2_pt_*`) | Authentication |
| `LANGSMITH_TRACING` | `true` | Enable tracing |
| `LANGSMITH_PROJECT` | `CODEFORGE` | Project name in LangSmith |
| `LANGSMITH_WORKSPACE_ID` | From LangSmith workspace URL | Route requests correctly |

> **Key type matters:** Use a **personal token** (`lsv2_pt_*`), not a service key (`lsv2_sk_*`).  
> Service keys may not have write access to sessions/runs.

## Optional: Flowise

| Variable | Value |
|----------|-------|
| `FLOWISE_API_KEY` | From Flowise Cloud settings |

## Pipeline Tuning

| Variable | Default | Effect |
|----------|---------|--------|
| `MODEL_NAME` | `llama-3.3-70b-versatile` | Groq model to use |
| `TEMPERATURE` | `0.1` | LLM temperature (lower = more deterministic) |
| `MAX_CODE_ITERATIONS` | `3` | Max times Reviewer can reject before forcing execution |
| `MAX_DEBUG_ATTEMPTS` | `3` | Max Debugger attempts before giving up |

## Example `.env`

```env
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...

LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=CODEFORGE
LANGSMITH_WORKSPACE_ID=a3025f62-...

MODEL_NAME=llama-3.3-70b-versatile
MAX_CODE_ITERATIONS=3
MAX_DEBUG_ATTEMPTS=3
TEMPERATURE=0.1
```
