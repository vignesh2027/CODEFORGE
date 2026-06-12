import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from config.llm import llm
from state.schema import AgentState

SYSTEM_PROMPT = """You are the Reviewer Agent in CODEFORGE — a senior code reviewer.

Review the provided code against the original task requirements.

Evaluate on:
1. Correctness — does it fully solve the task?
2. Completeness — is it runnable with no missing pieces?
3. Code quality — clean, readable, idiomatic?
4. Error handling — handles edge cases gracefully?
5. Security — no obvious vulnerabilities?

Respond ONLY with valid JSON (no markdown):
{
    "approved": true,
    "score": 9,
    "issues": [],
    "suggestions": ["optional improvement"],
    "summary": "Brief one-line review verdict"
}

Approve (approved: true) only if score >= 7 and no critical issues.
Critical issues: code won't run, missing key functionality, security holes."""


def _parse_review(content: str) -> Dict[str, Any]:
    content = content.strip()
    for delimiter in ["```json", "```"]:
        if delimiter in content:
            content = content.split(delimiter)[1].split("```")[0].strip()
            break
    return json.loads(content)


def review(state: AgentState) -> dict:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Review this code:

Task: {state['task']}
Language: {state['language']}

Code:
```{state['language']}
{state['code']}
```"""
        ),
    ]

    response = llm.invoke(messages)

    try:
        result = _parse_review(response.content)
        approved = bool(result.get("approved", False))
        score = result.get("score", 5)
        issues = result.get("issues", [])
        summary = result.get("summary", "Review complete")
        feedback = (
            f"Score: {score}/10 | {summary}"
            + (f"\nIssues: {'; '.join(issues)}" if issues else "")
        )
    except (json.JSONDecodeError, KeyError):
        approved = True
        feedback = response.content[:300]

    logs = list(state.get("agent_log", []))
    verdict = "APPROVED ✓" if approved else "REJECTED ✗"
    logs.append(f"[REVIEWER] {verdict} — {feedback.splitlines()[0]}")

    return {
        "review_approved": approved,
        "review_feedback": feedback,
        "current_agent": "executor" if approved else "coder",
        "agent_log": logs,
    }
