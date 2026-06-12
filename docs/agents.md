# Agent Reference

CODEFORGE runs six specialized agents in sequence. Each agent receives the full shared state and returns only the fields it modifies.

---

## 1. Orchestrator

**File:** `agents/orchestrator.py`  
**Role:** Analyze the raw user task and normalize it.

| Input | Output |
|-------|--------|
| `task` (raw string) | `task` (summarized), `language` (detected) |

**What it does:**
- Calls Groq with a strict JSON-response prompt
- Detects programming language (defaults to Python)
- Summarizes the task clearly for downstream agents

**Example output:**
```json
{"task_summary": "Implement a binary search tree with insert/search/delete", "language": "python"}
```

---

## 2. Planner

**File:** `agents/planner.py`  
**Role:** Turn the task summary into a step-by-step implementation plan.

| Input | Output |
|-------|--------|
| `task`, `language` | `plan` (numbered list) |

**What it does:**
- Creates 5–10 numbered steps
- Identifies required functions, classes, libraries
- Notes edge cases and error handling requirements

---

## 3. Coder

**File:** `agents/coder.py`  
**Role:** Write complete, runnable code based on the plan.

| Input | Output |
|-------|--------|
| `task`, `language`, `plan`, `review_feedback`, `debug_notes` | `code`, `code_iteration` |

**Tools:** Tavily Search (optional — used to look up documentation)

**What it does:**
- Uses `llm.bind_tools([search_tool])` for optional web search
- Runs an agentic loop: LLM → tool call → LLM → ... → final code
- Extracts code from fenced code blocks via regex
- Context-aware: reads `review_feedback` and `debug_notes` to fix previous issues

**Max tool calls per iteration:** 3

---

## 4. Reviewer

**File:** `agents/reviewer.py`  
**Role:** Score and approve/reject the generated code.

| Input | Output |
|-------|--------|
| `task`, `language`, `code` | `review_approved`, `review_feedback` |

**Scoring criteria:**
1. Correctness — solves the task?
2. Completeness — runnable with no missing pieces?
3. Code quality — clean, idiomatic?
4. Error handling — handles edge cases?
5. Security — no obvious vulnerabilities?

**Approval threshold:** score ≥ 7 AND no critical issues

**JSON response format:**
```json
{"approved": true, "score": 9, "issues": [], "summary": "..."}
```

---

## 5. Executor

**File:** `agents/executor.py`  
**Role:** Run the approved code and capture output.

| Input | Output |
|-------|--------|
| `code`, `language` | `execution_output`, `execution_success`, `final_code` |

**How it works:**
- Python only: writes code to a temp file, runs `subprocess.run([sys.executable, tmp])`
- 30-second timeout enforced
- Non-Python (JS, Java, etc.): marks success with a note, skips execution
- On success: sets `final_code`

---

## 6. Debugger

**File:** `agents/debugger.py`  
**Role:** Fix code that failed at runtime.

| Input | Output |
|-------|--------|
| `task`, `language`, `code`, `execution_output` | `code` (fixed), `debug_notes`, `debug_attempts` |

**What it does:**
- Receives the failed code + error message
- Identifies root cause (not just the symptom)
- Returns complete fixed code
- Increments `debug_attempts` (max 3 before giving up)

**Response format:**
```
DIAGNOSIS: <one-line root cause>

```python
<complete fixed code>
```
```
