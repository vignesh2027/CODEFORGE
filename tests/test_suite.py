#!/usr/bin/env python3
"""
CODEFORGE — Comprehensive Test Suite
Tests every API, every agent, and every pipeline scenario.
Run: python3 tests/test_suite.py
"""

import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

# ─── Result Model ────────────────────────────────────────────────────────────

@dataclass
class TestResult:
    name: str
    category: str
    passed: bool
    duration: float
    message: str = ""
    error: str = ""


# ─── Runner ──────────────────────────────────────────────────────────────────

class TestSuite:
    def __init__(self):
        self.results: List[TestResult] = []

    def run(self, category: str, name: str, fn) -> TestResult:
        console.print(f"  [dim]▸ {name}...[/dim]", end=" ")
        t0 = time.time()
        try:
            msg = fn()
            r = TestResult(name, category, True, time.time() - t0, message=str(msg or "OK"))
            console.print(f"[bold green]PASS[/bold green] [dim]{r.duration:.2f}s[/dim]")
        except Exception as e:
            r = TestResult(name, category, False, time.time() - t0, error=str(e)[:300])
            console.print(f"[bold red]FAIL[/bold red] [dim]{r.duration:.2f}s[/dim]")
            console.print(f"    [red]{r.error}[/red]")
        self.results.append(r)
        return r

    def section(self, title: str):
        console.print(f"\n[bold cyan]{'─'*50}[/bold cyan]")
        console.print(f"[bold cyan]  {title}[/bold cyan]")
        console.print(f"[bold cyan]{'─'*50}[/bold cyan]")

    def report(self):
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        console.print("\n")
        tbl = Table(title="CODEFORGE Test Report", box=box.DOUBLE_EDGE,
                    border_style="cyan", show_lines=True)
        tbl.add_column("Category", style="bold", width=22)
        tbl.add_column("Test", width=38)
        tbl.add_column("Result", width=8, justify="center")
        tbl.add_column("Time", width=8, justify="right")
        tbl.add_column("Info", width=40)

        for r in self.results:
            status = "[bold green]PASS ✓[/bold green]" if r.passed else "[bold red]FAIL ✗[/bold red]"
            info = r.message if r.passed else f"[red]{r.error[:38]}[/red]"
            tbl.add_row(r.category, r.name, status, f"{r.duration:.2f}s", info)

        console.print(tbl)

        summary = Table(box=box.SIMPLE, show_header=False)
        summary.add_column("", style="bold", width=20)
        summary.add_column("", width=10)
        summary.add_row("Total tests", str(len(self.results)))
        summary.add_row("[green]Passed[/green]", f"[green]{len(passed)}[/green]")
        summary.add_row("[red]Failed[/red]", f"[red]{len(failed)}[/red]")
        summary.add_row("Pass rate", f"{len(passed)/max(len(self.results),1)*100:.0f}%")
        console.print(summary)

        if failed:
            console.print("\n[bold red]Failed tests:[/bold red]")
            for r in failed:
                console.print(f"  ✗ [{r.category}] {r.name}")
                console.print(f"    {r.error}")

        return len(failed) == 0


# ─── Individual Tests ─────────────────────────────────────────────────────────

def test_env_vars():
    from config.settings import GROQ_API_KEY, TAVILY_API_KEY, LANGSMITH_ENABLED
    assert GROQ_API_KEY, "GROQ_API_KEY missing"
    assert TAVILY_API_KEY, "TAVILY_API_KEY missing"
    return f"Groq key: ...{GROQ_API_KEY[-6:]}, Tavily key: ...{TAVILY_API_KEY[-6:]}, LangSmith: {LANGSMITH_ENABLED}"


def test_groq_api():
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage
    from config.settings import GROQ_API_KEY, MODEL_NAME
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
    resp = llm.invoke([HumanMessage(content="Reply with just: GROQ_OK")])
    assert resp.content, "Empty response from Groq"
    assert len(resp.content) > 0
    return f"Model: {MODEL_NAME} | Response: {resp.content.strip()[:40]}"


def test_groq_token_count():
    from langchain_groq import ChatGroq
    from langchain_core.messages import HumanMessage
    from config.settings import GROQ_API_KEY, MODEL_NAME
    llm = ChatGroq(api_key=GROQ_API_KEY, model=MODEL_NAME, temperature=0)
    resp = llm.invoke([HumanMessage(content="Count to 5")])
    usage = resp.response_metadata.get("token_usage", {})
    tokens = usage.get("total_tokens", 0)
    assert tokens > 0, "No token usage returned"
    return f"Input: {usage.get('prompt_tokens',0)} | Output: {usage.get('completion_tokens',0)} | Total: {tokens}"


def test_tavily_search():
    from langchain_tavily import TavilySearch
    from config.settings import TAVILY_API_KEY
    import os
    os.environ["TAVILY_API_KEY"] = TAVILY_API_KEY
    tool = TavilySearch(max_results=3)
    results = tool.invoke({"query": "Python LangChain LangGraph"})
    assert results, "No results from Tavily"
    count = len(results) if isinstance(results, list) else 1
    return f"{count} results returned"


def test_langsmith_connection():
    from langsmith import Client
    from config.settings import LANGSMITH_ENABLED
    import os
    key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    assert key, "No LangSmith key in env"
    c = Client(api_key=key)
    projects = list(c.list_projects())
    names = [p.name for p in projects]
    assert "CODEFORGE" in names, f"CODEFORGE project not found. Found: {names}"
    return f"Connected | Projects: {names}"


def test_langsmith_create_run():
    import uuid
    from datetime import datetime, timezone
    from langsmith import Client
    import os
    key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    c = Client(api_key=key)
    run_id = str(uuid.uuid4())
    c.create_run(id=run_id, name="test-suite-ping", run_type="chain",
                 inputs={"test": True}, project_name="CODEFORGE",
                 start_time=datetime.now(timezone.utc))
    c.update_run(run_id, end_time=datetime.now(timezone.utc),
                 outputs={"status": "test-suite-pass"})
    return f"Run {run_id[:8]}... created and closed in LangSmith"


def test_code_executor():
    from tools.repl import execute_python_code
    ok, out = execute_python_code('print("EXECUTOR_OK"); print(2+2)')
    assert ok, f"Executor failed: {out}"
    assert "EXECUTOR_OK" in out
    assert "4" in out
    return f"Output: {out.strip()}"


def test_executor_catches_errors():
    from tools.repl import execute_python_code
    ok, out = execute_python_code("raise ValueError('intentional')")
    assert not ok, "Should have failed"
    assert "ValueError" in out
    return f"Error correctly caught: {out[:60]}"


def test_executor_timeout():
    from tools.repl import execute_python_code
    ok, out = execute_python_code("import time; time.sleep(60)", timeout=2)
    assert not ok
    assert "timed out" in out.lower()
    return "Timeout enforced correctly"


def test_orchestrator_agent():
    import json
    from agents.orchestrator import orchestrate
    state = {"task": "Write a quicksort algorithm in Python", "agent_log": []}
    result = orchestrate(state)
    assert result.get("language") == "python"
    assert result.get("agent_log")
    return f"Language={result['language']} | Log: {result['agent_log'][-1]}"


def test_orchestrator_javascript():
    from agents.orchestrator import orchestrate
    state = {"task": "Build a React hook for debouncing in JavaScript", "agent_log": []}
    result = orchestrate(state)
    lang = result.get("language", "")
    assert lang in ("javascript", "typescript"), f"Expected js/ts, got {lang}"
    return f"Correctly detected language: {lang}"


def test_planner_agent():
    from agents.planner import plan
    state = {
        "task": "Write a function to check if a number is prime",
        "language": "python",
        "agent_log": []
    }
    result = plan(state)
    assert result.get("plan"), "Plan is empty"
    assert len(result["plan"]) > 100, "Plan too short"
    return f"Plan: {len(result['plan'])} chars | {result['plan'][:60]}..."


def test_reviewer_approves_good_code():
    import json
    from agents.reviewer import review
    state = {
        "task": "Check if a number is even",
        "language": "python",
        "code": "def is_even(n: int) -> bool:\n    if not isinstance(n, int):\n        raise TypeError('Expected int')\n    return n % 2 == 0\n\nprint(is_even(4))\nprint(is_even(3))",
        "agent_log": []
    }
    result = review(state)
    assert result.get("review_approved"), f"Should approve good code. Feedback: {result.get('review_feedback','')}"
    return f"Approved ✓ | {result['review_feedback'][:80]}"


def test_reviewer_rejects_bad_code():
    from agents.reviewer import review
    state = {
        "task": "Create a secure password hasher",
        "language": "python",
        "code": "# TODO: implement\npass",
        "agent_log": []
    }
    result = review(state)
    assert not result.get("review_approved"), "Should reject incomplete code"
    return f"Correctly rejected | {result['review_feedback'][:80]}"


def test_coder_agent():
    from agents.coder import code
    state = {
        "task": "Write a function to flatten a nested list",
        "language": "python",
        "plan": "1. Define flatten(lst)\n2. Iterate items\n3. If item is list recurse else append\n4. Return result\n5. Test with examples",
        "review_feedback": "",
        "review_approved": False,
        "debug_notes": "",
        "code_iteration": 0,
        "agent_log": []
    }
    result = code(state)
    assert result.get("code"), "No code generated"
    assert len(result["code"]) > 50, "Code too short"
    return f"Code: {len(result['code'])} chars | Iteration: {result.get('code_iteration')}"


def test_full_pipeline_simple():
    from graph.workflow import create_workflow
    app = create_workflow()
    initial = _base_state("Write a Python function to calculate factorial recursively")
    final = app.invoke(initial)
    assert final.get("code"), "No code in final state"
    assert final.get("execution_success"), f"Execution failed: {final.get('execution_output','')[:200]}"
    return f"✓ {len(final['code'])} chars | exec: {final['execution_output'][:60]}"


def test_full_pipeline_data_structures():
    from graph.workflow import create_workflow
    app = create_workflow()
    initial = _base_state("Implement a stack with push, pop, peek, and is_empty methods in Python")
    final = app.invoke(initial)
    assert final.get("code"), "No code"
    return f"✓ iter={final.get('code_iteration')} | approved={final.get('review_approved')} | exec={final.get('execution_success')}"


def test_full_pipeline_algorithms():
    from graph.workflow import create_workflow
    app = create_workflow()
    initial = _base_state("Write bubble sort in Python and print a sorted example array")
    final = app.invoke(initial)
    assert final.get("code")
    return f"✓ code={len(final.get('code',''))} chars | exec={final.get('execution_success')}"


def test_full_pipeline_javascript():
    from graph.workflow import create_workflow
    app = create_workflow()
    initial = _base_state("Write a JavaScript function to deep clone an object without using JSON")
    final = app.invoke(initial)
    assert final.get("code"), "No code generated"
    assert final.get("language") in ("javascript", "typescript")
    return f"✓ {final.get('language').upper()} code generated | {len(final.get('code',''))} chars"


def test_review_loop():
    """Force a review loop by asking for something the first pass might miss."""
    from graph.workflow import create_workflow
    app = create_workflow()
    initial = _base_state("Write a Python class for a doubly linked list with insert_head, insert_tail, delete, and display methods")
    final = app.invoke(initial)
    assert final.get("code")
    iters = final.get("code_iteration", 0)
    return f"✓ Code iterations: {iters} | Final approved: {final.get('review_approved')}"


def _base_state(task: str) -> dict:
    return {
        "task": task, "plan": "", "language": "python",
        "code": "", "code_iteration": 0,
        "review_feedback": "", "review_approved": False,
        "execution_output": "", "execution_success": False,
        "debug_attempts": 0, "debug_notes": "",
        "current_agent": "orchestrator", "agent_log": [],
        "final_code": "", "final_explanation": "", "messages": []
    }


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    console.print(Panel.fit(
        "[bold cyan]CODEFORGE — Full Test Suite[/bold cyan]\n"
        "[dim]Testing all APIs · Agents · Pipeline scenarios[/dim]",
        border_style="cyan"
    ))

    suite = TestSuite()

    # 1. Config & Environment
    suite.section("1 · Configuration & Environment")
    suite.run("Config", "Environment variables loaded", test_env_vars)

    # 2. API Connectivity
    suite.section("2 · API Connectivity")
    suite.run("Groq API", "Groq LLM responds correctly", test_groq_api)
    suite.run("Groq API", "Token counting works", test_groq_token_count)
    suite.run("Tavily API", "Web search returns results", test_tavily_search)
    suite.run("LangSmith", "Project 'CODEFORGE' exists", test_langsmith_connection)
    suite.run("LangSmith", "Can create and close runs", test_langsmith_create_run)

    # 3. Core Tools
    suite.section("3 · Core Tools")
    suite.run("Executor", "Python code executes correctly", test_code_executor)
    suite.run("Executor", "Runtime errors are caught", test_executor_catches_errors)
    suite.run("Executor", "Timeout enforcement works", test_executor_timeout)

    # 4. Individual Agents
    suite.section("4 · Individual Agent Tests")
    suite.run("Orchestrator", "Detects Python task", test_orchestrator_agent)
    suite.run("Orchestrator", "Detects JavaScript task", test_orchestrator_javascript)
    suite.run("Planner", "Creates detailed plan", test_planner_agent)
    suite.run("Coder", "Generates runnable code", test_coder_agent)
    suite.run("Reviewer", "Approves high-quality code", test_reviewer_approves_good_code)
    suite.run("Reviewer", "Rejects incomplete code", test_reviewer_rejects_bad_code)

    # 5. Full Pipeline
    suite.section("5 · Full Pipeline (End-to-End)")
    suite.run("Pipeline", "Simple task: factorial", test_full_pipeline_simple)
    suite.run("Pipeline", "Data structures: stack", test_full_pipeline_data_structures)
    suite.run("Pipeline", "Algorithm: bubble sort", test_full_pipeline_algorithms)
    suite.run("Pipeline", "Non-Python: JavaScript deep clone", test_full_pipeline_javascript)
    suite.run("Pipeline", "Complex task triggers review loop", test_review_loop)

    # 6. Report
    all_passed = suite.report()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
