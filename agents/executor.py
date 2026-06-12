from state.schema import AgentState
from tools.repl import execute_python_code

_SKIPPED_LANGS = {"javascript", "typescript", "java", "cpp", "rust", "go"}


def execute(state: AgentState) -> dict:
    language = state["language"]
    code = state["code"]
    logs = list(state.get("agent_log", []))

    if language in _SKIPPED_LANGS:
        logs.append(
            f"[EXECUTOR] {language.upper()} code ready (execution: Python-only sandbox)"
        )
        return {
            "execution_output": f"Code generation complete. {language.upper()} execution is not supported in this sandbox.",
            "execution_success": True,
            "final_code": code,
            "current_agent": "done",
            "agent_log": logs,
        }

    success, output = execute_python_code(code)

    if success:
        logs.append(f"[EXECUTOR] Executed successfully ✓")
    else:
        snippet = output.splitlines()[-1][:80] if output else "unknown error"
        logs.append(f"[EXECUTOR] Execution failed ✗ — {snippet}")

    result: dict = {
        "execution_output": output,
        "execution_success": success,
        "agent_log": logs,
    }

    if success:
        result["final_code"] = code
        result["current_agent"] = "done"

    return result
