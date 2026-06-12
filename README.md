# CODEFORGE

> Multi-Agent Code Generation System — LangGraph + Groq + Tavily

CODEFORGE is an AI-powered multi-agent pipeline that transforms natural language task descriptions into clean, reviewed, and executed code. Six specialized agents collaborate in a LangGraph state machine to plan, write, review, run, and debug code automatically.

## Architecture

```
User Task
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│ ORCHESTRATOR │────▶│   PLANNER    │────▶│       CODER          │
│              │     │              │     │  + Tavily Web Search  │
│ Analyzes task│     │ Creates plan │     │  Writes code          │
└──────────────┘     └──────────────┘     └──────────┬───────────┘
                                                      │
                                                      ▼
                                          ┌──────────────────────┐
                                ◀─────────│      REVIEWER        │
                             rejected     │  Scores 1-10         │
                                          └──────────┬───────────┘
                                                      │ approved
                                                      ▼
                                          ┌──────────────────────┐
                                          │      EXECUTOR        │
                                          │  Runs in subprocess  │
                                          └──────────┬───────────┘
                                                      │
                                         ┌────────────┴────────────┐
                                      success                     fail
                                         │                          │
                                         ▼                          ▼
                                        END              ┌──────────────────┐
                                                         │    DEBUGGER      │
                                                         │  Diagnoses & fixes│
                                                         └──────────────────┘
                                                                   │
                                                                   └──▶ CODER
```

## Agents

| Agent | Role | Tools |
|-------|------|-------|
| **Orchestrator** | Analyzes the task, determines programming language | — |
| **Planner** | Creates a step-by-step implementation plan | — |
| **Coder** | Writes complete, production-quality code | Tavily Search |
| **Reviewer** | Scores code 1–10, approves or rejects | — |
| **Executor** | Runs code in an isolated subprocess | Python Subprocess |
| **Debugger** | Diagnoses runtime errors and applies fixes | — |

## Features

- **6 Specialized Agents** — Each agent has a single, focused responsibility
- **Web Search** — Coder searches documentation via Tavily before writing
- **Auto-Review Loop** — Reviewer rejects code until quality score ≥ 7/10 (up to 3 iterations)
- **Auto-Debug Loop** — Debugger fixes runtime errors automatically (up to 3 attempts)
- **Isolated Execution** — Code runs in a sandboxed subprocess, not the main process
- **Rich Terminal UI** — Syntax-highlighted output, agent activity table, run statistics
- **Multi-Language** — Python (with execution), JavaScript, TypeScript, Java, C++, Rust, Go

## Setup

```bash
git clone https://github.com/vignesh2027/CODEFORGE.git
cd CODEFORGE
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your API keys
python main.py
```

## API Keys

| Service | Purpose | Get it at |
|---------|---------|-----------|
| Groq | LLM inference (Llama 3.3 70B) | console.groq.com |
| Tavily | Real-time web search | app.tavily.com |

Both have generous free tiers. LangChain itself needs no API key — it's open-source.

## Configuration (`.env`)

```env
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
MODEL_NAME=llama-3.3-70b-versatile
MAX_CODE_ITERATIONS=3
MAX_DEBUG_ATTEMPTS=3
TEMPERATURE=0.1
```

## Usage

```bash
# Interactive prompt
python main.py

# Inline task
python main.py "Write a binary search tree with insert, search, and delete in Python"
python main.py "Build a rate limiter using the token bucket algorithm"
python main.py "Create a CSV parser that handles quoted fields with embedded commas"
python main.py "Implement a simple LRU cache with get and put operations"
```

## Example Output

```
  [ORCHESTRATOR] Task analyzed → Language: PYTHON
  [PLANNER] Implementation plan created
  [CODER] Code written — iteration 1 (searched web 1x)
  [REVIEWER] APPROVED ✓ — Score: 9/10 | Clean implementation, all edge cases handled
  [EXECUTOR] Executed successfully ✓

Generated PYTHON Code
╭──────────────────────────────────────────────────────────────────╮
│   1 │ class Node:                                                 │
│   2 │     def __init__(self, key, val):                           │
│   3 │         self.key, self.val = key, val                       │
│   4 │         self.prev = self.next = None                        │
│  ...│                                                             │
╰──────────────────────────────────────────────────────────────────╯

Run Statistics
  Language          PYTHON
  Code iterations   1
  Debug attempts    0
  Review approved   YES ✓
  Execution         SUCCESS ✓
  Total time        12.4s
```

## Tech Stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — Multi-agent state machine orchestration
- **[LangChain](https://github.com/langchain-ai/langchain)** — LLM framework (open-source, no API key needed)
- **[Groq](https://groq.com)** — Ultra-fast LLM inference
- **[Tavily](https://tavily.com)** — Real-time web search API
- **[Rich](https://github.com/Textualize/rich)** — Terminal UI

## License

MIT License — Copyright (c) 2024 Vignesh S
