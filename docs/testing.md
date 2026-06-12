# Testing Guide

CODEFORGE includes a comprehensive test suite covering all APIs, agents, and pipeline scenarios.

## Run All Tests

```bash
cd CODEFORGE
python3 tests/test_suite.py
```

## Test Categories

### 1. Configuration (1 test)
- Environment variables loaded correctly

### 2. API Connectivity (5 tests)
- Groq LLM responds correctly
- Groq token counting works
- Tavily web search returns results
- LangSmith project `CODEFORGE` exists
- LangSmith can create and close runs

### 3. Core Tools (3 tests)
- Python executor runs code correctly
- Executor catches runtime errors
- Executor enforces 30s timeout

### 4. Individual Agents (6 tests)
- Orchestrator detects Python task
- Orchestrator detects JavaScript task
- Planner creates detailed plan (>100 chars)
- Coder generates runnable code
- Reviewer approves high-quality code
- Reviewer rejects incomplete code

### 5. Full Pipeline (5 tests)
- Simple task: factorial function
- Data structures: stack implementation
- Algorithm: bubble sort with output
- Non-Python: JavaScript deep clone
- Complex task: doubly linked list (tests review loop)

## Test Results (Last Run)

```
Total tests : 20
Passed      : 20
Failed      :  0
Pass rate   : 100%
```

All tests pass, including 5 full end-to-end pipeline runs. The `max_retries=3`
config on ChatGroq handles transient Groq TPM rate limits automatically.

## Adding New Tests

Add a new function to `tests/test_suite.py`:

```python
def test_my_new_feature():
    # raises exception on failure
    result = my_function()
    assert result == expected, f"Got {result}"
    return f"Descriptive success message"

# Then register it in main():
suite.run("Category", "My feature description", test_my_new_feature)
```
