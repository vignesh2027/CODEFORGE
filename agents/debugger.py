import re

from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import llm
from state.schema import AgentState

SYSTEM_PROMPT = """You are the Debugger Agent in CODEFORGE — an expert at diagnosing and fixing runtime errors.

You will receive code that failed during execution along with the error output.

Your job:
1. Diagnose the root cause of the error (not just the symptom)
2. Apply a complete fix — not a patch, a proper solution
3. Ensure the fixed code handles the error case going forward

Respond in this exact format:

DIAGNOSIS: <one-line root cause explanation>

```language
<complete fixed code — no truncation>
```"""


def _extract_code(text: str, language: str) -> str:
    patterns = [
        rf"```{re.escape(language)}\n(.*?)```",
        r"```\w+\n(.*?)```",
        r"```\n(.*?)```",
        r"```(.*?)```",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    return text.strip()


def debug(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Fix this failing code:

Task: {state['task']}
Language: {state['language']}

Code that failed:
```{state['language']}
{state['code']}
```

Error output:
{state['execution_output']}

Diagnose and provide the complete fixed code."""
        ),
    ]

    response = llm.invoke(messages)
    fixed_code = _extract_code(response.content, state["language"])

    diagnosis = ""
    if "DIAGNOSIS:" in response.content:
        line = response.content.split("DIAGNOSIS:")[1].split("\n")[0]
        diagnosis = line.strip()

    attempts = state.get("debug_attempts", 0) + 1
    logs = list(state.get("agent_log", []))
    diag_preview = diagnosis[:70] if diagnosis else "fix applied"
    logs.append(f"[DEBUGGER] Attempt {attempts} — {diag_preview}")

    return {
        "code": fixed_code,
        "debug_attempts": attempts,
        "debug_notes": response.content,
        "current_agent": "coder",
        "agent_log": logs,
    }
