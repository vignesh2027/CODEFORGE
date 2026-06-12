<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=700&size=32&pause=1000&color=C17830&center=true&vCenter=true&width=600&lines=CODEFORGE;Multi-Agent+Code+Generation;Plan+%E2%86%92+Write+%E2%86%92+Review+%E2%86%92+Ship" alt="CODEFORGE" />

<p><strong>A 6-agent LangGraph system that autonomously plans, writes, reviews, executes, and debugs code.</strong><br/>
Powered by Groq Llama 3.3 70B · Tavily Web Search · LangSmith Observability</p>

[![Tests](https://img.shields.io/badge/tests-20%2F20%20passing-brightgreen?style=flat-square&logo=pytest)](https://github.com/vignesh2027/CODEFORGE/blob/main/tests/test_suite.py)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2-orange?style=flat-square)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-red?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)
[![Pages](https://img.shields.io/badge/docs-live-C17830?style=flat-square)](https://vignesh2027.github.io/CODEFORGE)

[**Live Demo Site →**](https://vignesh2027.github.io/CODEFORGE) · [**Full Docs →**](https://vignesh2027.github.io/CODEFORGE/docs.html) · [**Flowise Canvas →**](https://cloud.flowiseai.com/canvas/7b4a8af4-0126-4869-8046-1e70f0ff0d05) · [**LangSmith →**](https://smith.langchain.com)

</div>

---

## What is CODEFORGE?

CODEFORGE is a **production-grade multi-agent AI system** that takes a plain-English coding task and returns complete, reviewed, and executed code — fully automatically.

You type: _"Implement a binary search tree with insert, search, and delete"_

CODEFORGE returns: working, tested, production-quality Python code in under 10 seconds.

### Why it's different

| Feature | CODEFORGE | Typical AI Codegen |
|---|---|---|
| Self-reviewing | ✅ Scores own code 1–10, rewrites if < 7 | ❌ Single shot |
| Web search while coding | ✅ Tavily lookup during generation | ❌ Static knowledge |
| Execution + auto-debug | ✅ Runs code, fixes errors automatically | ❌ No execution |
| Full observability | ✅ Every trace in LangSmith | ❌ Black box |
| Visual pipeline | ✅ Flowise canvas | ❌ None |
| Multi-platform | ✅ Terminal + Flowise + API | ❌ None |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CODEFORGE Pipeline                          │
│                                                                     │
│  User Task                                                          │
│      │                                                              │
│      ▼                                                              │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────────────────────┐  │
│  │ ORCHESTRATOR│──▶│   PLANNER   │──▶│         CODER            │  │
│  │             │   │             │   │  + Tavily web search      │  │
│  │ • detect    │   │ • 5–10 step │   │  • reads review feedback  │◀─┤
│  │   language  │   │   plan      │   │  • reads debug notes      │  │
│  │ • summarize │   │ • edge cases│   │  • writes complete code   │  │
│  └─────────────┘   └─────────────┘   └──────────┬───────────────┘  │
│                                                  │                  │
│                                                  ▼                  │
│                                      ┌──────────────────────────┐  │
│                              ◀───────│        REVIEWER          │  │
│                           (score<7)  │  • scores code 1–10      │  │
│                                      │  • 5 quality criteria    │  │
│                                      │  • max 3 review rounds   │  │
│                                      └──────────┬───────────────┘  │
│                                                  │ (score ≥ 7)     │
│                                                  ▼                  │
│                                      ┌──────────────────────────┐  │
│                                      │        EXECUTOR          │  │
│                                      │  • subprocess isolation  │  │
│                                      │  • 30s hard timeout      │  │
│                                      └──────┬──────────┬────────┘  │
│                                             │          │           │
│                                          success      fail         │
│                                             │          │           │
│                                             ▼          ▼           │
│                                            END    ┌─────────────┐  │
│                                                   │  DEBUGGER   │  │
│                                                   │ • root cause│  │
│                                                   │ • fix+retry │  │
│                                                   │ • max 3x    │  │
│                                                   └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

Every agent shares a single `AgentState` TypedDict via LangGraph's StateGraph. Each agent reads the full state and writes only the fields it owns.

---

## The 6 Agents

### 1. Orchestrator
Reads the raw task → detects language → writes a clean task summary for downstream agents.
**Writes:** `task` (summarized), `language`

### 2. Planner
Turns the task summary into a numbered blueprint: functions, classes, libraries, and edge cases.
**Writes:** `plan`

### 3. Coder
Writes production-quality code following the plan. Equipped with **Tavily web search** — can look up current docs mid-generation. Reads `review_feedback` and `debug_notes` to fix prior attempts.
**Writes:** `code`, `code_iteration` · **Tools:** TavilySearch

### 4. Reviewer
Scores code 1–10 across five axes: correctness, completeness, quality, error handling, security. Score ≥ 7 → approved. Score < 7 → returns feedback to Coder. Max 3 rounds.
**Writes:** `review_approved`, `review_feedback`

### 5. Executor
Writes code to a temp file and runs it via `subprocess.run()` with a 30s hard timeout. Non-Python languages skip execution and are marked successful.
**Writes:** `execution_output`, `execution_success`, `final_code`

### 6. Debugger
Receives failed code + error traceback → diagnoses root cause → returns a complete fixed version → loops back to Executor. Max 3 attempts.
**Writes:** `code` (fixed), `debug_notes`, `debug_attempts`

---

## Quick Start

### Prerequisites
- Python 3.10+
- Groq API key — [console.groq.com](https://console.groq.com) (free)
- Tavily API key — [app.tavily.com](https://app.tavily.com) (free)

### Install

```bash
git clone https://github.com/vignesh2027/CODEFORGE.git
cd CODEFORGE
pip install -r requirements.txt
cp .env.example .env
# fill in your keys in .env
python3 main.py
```

### Run tests

```bash
python3 tests/test_suite.py
# Expected: 20/20 passing
```

---

## Example Tasks

```bash
# Data structures
"Implement a min-heap with insert, extract_min, and heapify"
"Build a trie for autocomplete with insert and search"
"Create an AVL tree with self-balancing rotations"

# Algorithms
"Write Dijkstra's shortest path algorithm with priority queue"
"Implement merge sort with time complexity benchmarks"
"Build a dynamic programming solution for the knapsack problem"

# Systems
"Build a thread-safe LRU cache with get and put"
"Create a rate limiter using the token bucket algorithm"
"Implement a simple pub/sub event system in Python"

# APIs & parsing
"Write a CSV parser that handles quoted fields with embedded commas"
"Build a JSON schema validator from scratch"
"Create a URL parser that extracts scheme, host, path, and query"
```

---

## Configuration

All config via `.env`. See [docs/configuration.md](docs/configuration.md) for full reference.

| Variable | Default | Required |
|---|---|---|
| `GROQ_API_KEY` | — | ✅ Yes |
| `TAVILY_API_KEY` | — | ✅ Yes |
| `MODEL_NAME` | `llama-3.3-70b-versatile` | No |
| `TEMPERATURE` | `0.1` | No |
| `MAX_CODE_ITERATIONS` | `3` | No |
| `MAX_DEBUG_ATTEMPTS` | `3` | No |
| `LANGSMITH_API_KEY` | — | No (optional tracing) |
| `LANGSMITH_TRACING` | `false` | No |

---

## Test Suite

```bash
python3 tests/test_suite.py
```

| Category | Tests | Status |
|---|---|---|
| Configuration | Env vars, key presence | ✅ |
| API Connectivity | Groq, Tavily, LangSmith | ✅ |
| Core Tools | Execution, timeout, error catching | ✅ |
| Individual Agents | Each agent in isolation | ✅ |
| Full Pipeline | 5 end-to-end scenarios | ✅ |
| **Total** | **20 tests** | **✅ 100%** |

---

## Integrations

**LangSmith** — Set `LANGSMITH_TRACING=true` to trace every agent call to [smith.langchain.com](https://smith.langchain.com).

**Flowise** — Deploy a visual chat interface in one command:
```bash
python3 flowise/create_flow.py
```

---

## Project Structure

```
CODEFORGE/
├── main.py                 ← entry point
├── requirements.txt
├── .env.example
├── state/schema.py         ← AgentState TypedDict
├── config/
│   ├── settings.py         ← env loader, LangSmith setup
│   └── llm.py              ← ChatGroq factory
├── agents/
│   ├── orchestrator.py     ← Agent 1
│   ├── planner.py          ← Agent 2
│   ├── coder.py            ← Agent 3 (+ Tavily)
│   ├── reviewer.py         ← Agent 4
│   ├── executor.py         ← Agent 5
│   └── debugger.py         ← Agent 6
├── tools/
│   ├── search.py           ← Tavily wrapper
│   └── repl.py             ← subprocess executor
├── graph/workflow.py       ← LangGraph StateGraph
├── flowise/create_flow.py  ← Flowise canvas builder
├── tests/test_suite.py     ← 20-test suite
└── docs/                   ← GitHub Pages site
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq — Llama 3.3 70B Versatile |
| Orchestration | LangGraph 0.2 |
| LLM Framework | LangChain 0.3 |
| Web Search | Tavily Search API |
| Observability | LangSmith |
| Visual Canvas | Flowise Cloud |
| Terminal UI | Rich |
| Code Execution | Python subprocess |
| Docs | GitHub Pages + GitHub Actions |

---

## Documentation

| Resource | Link |
|---|---|
| Live site | [vignesh2027.github.io/CODEFORGE](https://vignesh2027.github.io/CODEFORGE) |
| Full docs | [vignesh2027.github.io/CODEFORGE/docs.html](https://vignesh2027.github.io/CODEFORGE/docs.html) |
| Agent reference | [docs/agents.md](docs/agents.md) |
| Configuration | [docs/configuration.md](docs/configuration.md) |
| Testing guide | [docs/testing.md](docs/testing.md) |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — issues, PRs, and feedback welcome.

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
Built by <a href="https://github.com/vignesh2027">Vignesh S</a> · Takshashila University, CSE 2022–26
</div>
