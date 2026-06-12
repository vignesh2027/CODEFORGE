#!/usr/bin/env python3
"""CODEFORGE — Multi-Agent Code Generation System"""

import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table

from config.settings import LANGSMITH_ENABLED  # must import before graph
from graph.workflow import create_workflow
from state.schema import AgentState

console = Console()

BANNER = r"""
  ██████╗ ██████╗ ██████╗ ███████╗███████╗ ██████╗ ██████╗  ██████╗ ███████╗
 ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
 ██║     ██║   ██║██║  ██║█████╗  █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
 ██║     ██║   ██║██║  ██║██╔══╝  ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
 ╚██████╗╚██████╔╝██████╔╝███████╗██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
"""

AGENT_COLORS = {
    "ORCHESTRATOR": "cyan",
    "PLANNER": "blue",
    "CODER": "yellow",
    "REVIEWER": "magenta",
    "EXECUTOR": "green",
    "DEBUGGER": "red",
}


def _print_banner() -> None:
    console.print(f"[bold cyan]{BANNER}[/bold cyan]")
    console.print(
        Panel.fit(
            "[bold white]Multi-Agent Code Generation System[/bold white]\n"
            "[dim]Orchestrator → Planner → Coder → Reviewer → Executor → Debugger[/dim]\n"
            "[dim cyan]LangGraph  ·  Groq Llama 3.3 70B  ·  Tavily Search[/dim cyan]",
            border_style="cyan",
        )
    )


def _print_log(log: str) -> None:
    for tag, color in AGENT_COLORS.items():
        if f"[{tag}]" in log:
            console.print(f"  [{color}]{log}[/{color}]")
            return
    console.print(f"  {log}")


def _print_results(state: AgentState, elapsed: float) -> None:
    console.print("\n" + "─" * 72 + "\n")

    # Agent activity table
    if state.get("agent_log"):
        tbl = Table(title="Agent Activity Log", border_style="dim", show_lines=False)
        tbl.add_column("Agent", style="bold", width=14)
        tbl.add_column("Status")
        for log in state["agent_log"]:
            parts = log.split("]", 1)
            if len(parts) == 2:
                tag = parts[0].replace("[", "").strip()
                color = AGENT_COLORS.get(tag, "white")
                tbl.add_row(f"[{color}]{tag}[/{color}]", parts[1].strip())
        console.print(tbl)
        console.print()

    # Generated code
    code = state.get("final_code") or state.get("code", "")
    language = state.get("language", "python")
    if code:
        console.print(
            Panel(
                Syntax(code, language, theme="monokai", line_numbers=True),
                title=f"[bold green]Generated {language.upper()} Code[/bold green]",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Execution output
    exec_out = state.get("execution_output", "")
    exec_ok = state.get("execution_success", False)
    if exec_out:
        color = "green" if exec_ok else "red"
        label = "SUCCESS ✓" if exec_ok else "FAILED ✗"
        console.print(
            Panel(
                exec_out,
                title=f"[bold {color}]Execution: {label}[/bold {color}]",
                border_style=color,
            )
        )

    # Run stats
    stats = Table(title="Run Statistics", border_style="dim", show_header=False)
    stats.add_column("", style="dim", width=20)
    stats.add_column("", style="bold white")
    stats.add_row("Language", language.upper())
    stats.add_row("Code iterations", str(state.get("code_iteration", 0)))
    stats.add_row("Debug attempts", str(state.get("debug_attempts", 0)))
    stats.add_row("Review approved", "YES ✓" if state.get("review_approved") else "NO ✗")
    stats.add_row("Execution", "SUCCESS ✓" if exec_ok else "FAILED / SKIPPED")
    stats.add_row("Total time", f"{elapsed:.1f}s")
    console.print(stats)


def run(task: str) -> AgentState:
    app = create_workflow()

    initial: AgentState = {
        "task": task,
        "plan": "",
        "language": "python",
        "code": "",
        "code_iteration": 0,
        "review_feedback": "",
        "review_approved": False,
        "execution_output": "",
        "execution_success": False,
        "debug_attempts": 0,
        "debug_notes": "",
        "current_agent": "orchestrator",
        "agent_log": [],
        "final_code": "",
        "final_explanation": "",
        "messages": [],
    }

    console.print("\n[bold yellow]⚡ Launching agents...[/bold yellow]\n")

    final_state = dict(initial)
    seen_logs: int = 0

    for full_state in app.stream(initial, stream_mode="values"):
        final_state = dict(full_state)
        logs = final_state.get("agent_log", [])
        for log in logs[seen_logs:]:
            _print_log(log)
        seen_logs = len(logs)

    return final_state  # type: ignore[return-value]


def main() -> None:
    _print_banner()

    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
        console.print(f"\n[bold]Task:[/bold] {task}\n")
    else:
        console.print("\n[bold cyan]What would you like to build?[/bold cyan]")
        task = Prompt.ask("[dim]Describe your coding task[/dim]")

    if not task.strip():
        console.print("[red]No task provided. Exiting.[/red]")
        sys.exit(1)

    t0 = time.time()
    final_state = run(task)
    _print_results(final_state, time.time() - t0)


if __name__ == "__main__":
    main()
