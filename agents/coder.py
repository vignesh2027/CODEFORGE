import re
from typing import List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from config.llm import llm
from config.settings import MAX_CODE_ITERATIONS
from state.schema import AgentState
from tools.search import search_tool

SYSTEM_PROMPT = """You are the Coder Agent in CODEFORGE — an expert software engineer.

Write complete, production-quality code based on the given plan.

You have access to a web search tool. Use it to:
- Look up library documentation or API usage
- Find code examples for unfamiliar patterns
- Verify the best approach for a specific problem

Code guidelines:
- Write COMPLETE, runnable code — no placeholders or pseudocode
- Include proper error handling and input validation
- Follow language-specific best practices and idioms
- Add comments only where the logic is non-obvious

Return ONLY the code wrapped in a fenced code block:
```language
<complete code here>
```

No explanations outside the code block."""


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


def _build_context(state: AgentState) -> str:
    parts = []

    if state.get("review_feedback") and not state.get("review_approved"):
        parts.append(
            f"\n\nPrevious code was REJECTED by the Reviewer.\nFeedback:\n{state['review_feedback']}\n\nFix all issues mentioned above."
        )

    if state.get("debug_notes"):
        parts.append(
            f"\n\nDebugger analysis:\n{state['debug_notes']}\n\nApply the fix described above."
        )

    return "".join(parts)


def code(state: AgentState) -> dict:
    llm_with_tools = llm.bind_tools([search_tool])
    context = _build_context(state)

    messages: List = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Task: {state['task']}
Language: {state['language']}

Implementation Plan:
{state['plan']}
{context}

Write the complete implementation now."""
        ),
    ]

    tool_calls_made = 0
    max_tool_calls = 3
    final_response = None

    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not response.tool_calls or tool_calls_made >= max_tool_calls:
            final_response = response
            break

        for tc in response.tool_calls:
            tool_calls_made += 1
            result = search_tool.invoke(tc["args"])
            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tc["id"],
                    name=tc["name"],
                )
            )

    generated_code = _extract_code(final_response.content, state["language"])
    iteration = state.get("code_iteration", 0) + 1

    logs = list(state.get("agent_log", []))
    search_note = f" (searched web {tool_calls_made}x)" if tool_calls_made else ""
    logs.append(f"[CODER] Code written — iteration {iteration}{search_note}")

    return {
        "code": generated_code,
        "code_iteration": iteration,
        "review_approved": False,
        "review_feedback": "",
        "current_agent": "reviewer",
        "agent_log": logs,
    }
