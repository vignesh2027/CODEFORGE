#!/usr/bin/env python3
"""
Creates the CODEFORGE multi-agent pipeline inside Flowise Cloud.
Run: python3 flowise/create_flow.py
"""
import json, sys, os, requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FLOWISE_URL = "https://cloud.flowiseai.com"
FLOWISE_KEY = "BkV4qapsZW6FUoVHdASgmcyEeaRyUy9XkFYqYjKFQ8U"
HEADERS = {"Authorization": f"Bearer {FLOWISE_KEY}", "Content-Type": "application/json"}


def api(method, path, body=None):
    url = f"{FLOWISE_URL}{path}"
    fn = {"GET": requests.get, "POST": requests.post,
          "PUT": requests.put, "DELETE": requests.delete}[method]
    r = fn(url, headers=HEADERS, json=body, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"{method} {path} → {r.status_code}: {r.text[:300]}")
    return r.json()


def delete_existing(name):
    flows = api("GET", "/api/v1/chatflows")
    for f in flows:
        if f.get("name") == name:
            try:
                api("DELETE", f"/api/v1/chatflows/{f['id']}")
                print(f"  Deleted old flow: {f['id']}")
            except Exception:
                pass


# ── Node builder helpers ───────────────────────────────────────────────────────

def agentflow_node(node_id, node_type, label, x, y, inputs=None, outputs=None):
    return {
        "id": node_id,
        "position": {"x": x, "y": y},
        "type": "agentFlow",
        "data": {
            "id": node_id,
            "label": label,
            "name": node_type,
            "version": 1,
            "type": "agentFlow",
            "category": "Agent Flows",
            "baseClasses": ["AgentFlow"],
            "inputs": inputs or {},
            "outputs": outputs or {"output": f"{node_id}-output-0"},
            "selected": False,
        },
        "width": 210,
        "height": 110,
        "selected": False,
        "dragging": False,
    }


def custom_node(node_id, node_type, label, category, x, y, inputs=None, outputs=None, credential=None):
    data = {
        "id": node_id,
        "label": label,
        "name": node_type,
        "version": 1,
        "type": node_type,
        "category": category,
        "baseClasses": [node_type, "BaseChatModel", "BaseLanguageModel"],
        "inputs": inputs or {},
        "outputs": outputs or {},
        "selected": False,
    }
    if credential:
        data["credential"] = credential
    return {
        "id": node_id,
        "position": {"x": x, "y": y},
        "type": "customNode",
        "data": data,
        "width": 210,
        "height": 110,
        "selected": False,
    }


def edge(eid, src, tgt, src_handle=None, tgt_handle=None):
    return {
        "id": eid,
        "source": src,
        "target": tgt,
        "sourceHandle": src_handle or f"{src}-output-0",
        "targetHandle": tgt_handle or f"{tgt}-input-0",
        "type": "buttonedge",
        "animated": True,
        "selected": False,
    }


# ── System prompts ─────────────────────────────────────────────────────────────

ORCHESTRATOR_PROMPT = """You are the 🎯 ORCHESTRATOR Agent in CODEFORGE — a multi-agent code generation system.

Analyze the user's coding task:
1. Identify the programming language (default: Python if not mentioned)
2. Summarize what needs to be built clearly and concisely
3. Identify key requirements

Reply with: [LANGUAGE: python] followed by a clear task summary."""

PLANNER_PROMPT = """You are the 📋 PLANNER Agent in CODEFORGE.

Create a numbered step-by-step implementation plan for the coding task.
Cover: required functions/classes, libraries, error handling, edge cases.
Be specific and actionable."""

CODER_PROMPT = """You are the 💻 CODER Agent in CODEFORGE — an expert software engineer.

Write COMPLETE, production-quality code based on the conversation context.
Rules:
- No pseudocode or placeholders — fully runnable
- Include proper error handling
- Follow language best practices
- Wrap code in ```language blocks

Return ONLY the code block, no extra explanation."""

REVIEWER_PROMPT = """You are the 🔍 REVIEWER Agent in CODEFORGE.

Review the code for: correctness, completeness, quality (1-10), error handling, security.

Respond in JSON:
{"approved": true/false, "score": 8, "issues": [], "summary": "..."}

Approve (true) only if score >= 7 and no critical issues."""

EXECUTOR_PROMPT = """You are the ⚡ EXECUTOR Agent in CODEFORGE.

The code has been reviewed and approved. Your job:
1. Confirm the code is ready to run
2. Describe what the code does and its expected output
3. List any setup steps needed (pip installs, etc.)
4. Provide a sample run command

Present the final working code clearly."""


def build_flow():
    """Build a complete CODEFORGE 6-agent Flowise agentflow."""

    # ── Groq Chat Model (shared by all LLM agents) ─────────────────────────
    groq_node = custom_node(
        "groqChat_0", "groqChat", "⚡ ChatGroq — Llama 3.3 70B",
        "Chat Models", 700, 700,
        inputs={
            "modelName": "llama-3.3-70b-versatile",
            "temperature": 0.1,
            "streaming": True,
            "maxTokens": 4096,
        },
        outputs={"output": "groqChat_0-output-ChatGroq-BaseLanguageModel"},
    )

    # ── Tavily Search Tool ──────────────────────────────────────────────────
    tavily_node = custom_node(
        "tavily_0", "tavilyAPI", "🔎 Tavily Search",
        "Tools", 900, 700,
        inputs={
            "maxResults": 5,
            "searchDepth": "basic",
            "topic": "general",
        },
        outputs={"output": "tavily_0-output-TavilySearch-Tool"},
    )

    # ── Agent Flow Nodes ────────────────────────────────────────────────────
    start = agentflow_node("start_0", "startAgentflow", "▶ START", 80, 340,
        inputs={"startInputType": "chatInput"},
        outputs={"output": "start_0-output-0"})

    orchestrator = agentflow_node("orchestrator_0", "llmAgentflow", "🎯 ORCHESTRATOR", 360, 340,
        inputs={
            "llmModel": "{{groqChat_0.data.instance}}",
            "llmMessages": [{"role": "system", "content": ORCHESTRATOR_PROMPT}],
            "llmReturnResponseAs": "userMessage",
            "llmEnableMemory": True,
            "llmMemoryType": "allMessages",
        })

    planner = agentflow_node("planner_0", "llmAgentflow", "📋 PLANNER", 640, 340,
        inputs={
            "llmModel": "{{groqChat_0.data.instance}}",
            "llmMessages": [{"role": "system", "content": PLANNER_PROMPT}],
            "llmReturnResponseAs": "userMessage",
            "llmEnableMemory": True,
            "llmMemoryType": "allMessages",
        })

    coder = agentflow_node("coder_0", "llmAgentflow", "💻 CODER", 920, 340,
        inputs={
            "llmModel": "{{groqChat_0.data.instance}}",
            "llmMessages": [{"role": "system", "content": CODER_PROMPT}],
            "llmReturnResponseAs": "userMessage",
            "llmEnableMemory": True,
            "llmMemoryType": "allMessages",
        })

    reviewer = agentflow_node("reviewer_0", "llmAgentflow", "🔍 REVIEWER", 1200, 340,
        inputs={
            "llmModel": "{{groqChat_0.data.instance}}",
            "llmMessages": [{"role": "system", "content": REVIEWER_PROMPT}],
            "llmReturnResponseAs": "userMessage",
            "llmEnableMemory": True,
            "llmMemoryType": "allMessages",
        })

    condition = agentflow_node("condition_0", "conditionAgentflow", "❓ APPROVED?", 1480, 340,
        inputs={
            "conditions": [{"type": "string", "value1": "{{reviewer_0.output}}",
                           "operation": "contains", "value2": "true"}]
        },
        outputs={"true": "condition_0-output-true", "false": "condition_0-output-false"})

    executor = agentflow_node("executor_0", "llmAgentflow", "⚡ EXECUTOR", 1760, 200,
        inputs={
            "llmModel": "{{groqChat_0.data.instance}}",
            "llmMessages": [{"role": "system", "content": EXECUTOR_PROMPT}],
            "llmReturnResponseAs": "userMessage",
            "llmEnableMemory": True,
            "llmMemoryType": "allMessages",
        })

    debugger = agentflow_node("debugger_0", "llmAgentflow", "🐛 DEBUGGER", 1760, 500,
        inputs={
            "llmModel": "{{groqChat_0.data.instance}}",
            "llmMessages": [{"role": "system", "content": (
                "You are the 🐛 DEBUGGER Agent in CODEFORGE. "
                "The code was rejected by the reviewer. "
                "Analyze the review feedback and fix ALL issues. "
                "Return the complete corrected code in a ```language block."
            )}],
            "llmReturnResponseAs": "userMessage",
            "llmEnableMemory": True,
            "llmMemoryType": "allMessages",
        })

    end_success = agentflow_node("end_success_0", "directReplyAgentflow", "✅ DONE", 2040, 200,
        inputs={}, outputs={"output": "end_success_0-output-0"})

    nodes = [start, orchestrator, planner, coder, reviewer,
             condition, executor, debugger, end_success, groq_node, tavily_node]

    edges = [
        edge("e1", "start_0",       "orchestrator_0"),
        edge("e2", "orchestrator_0", "planner_0"),
        edge("e3", "planner_0",     "coder_0"),
        edge("e4", "coder_0",       "reviewer_0"),
        edge("e5", "reviewer_0",    "condition_0"),
        edge("e6-yes", "condition_0", "executor_0",
             "condition_0-output-true", "executor_0-input-0"),
        edge("e6-no",  "condition_0", "debugger_0",
             "condition_0-output-false", "debugger_0-input-0"),
        edge("e7", "executor_0",    "end_success_0"),
        edge("e8", "debugger_0",    "coder_0",
             "debugger_0-output-0", "coder_0-input-0"),
    ]

    return json.dumps({
        "nodes": nodes,
        "edges": edges,
        "viewport": {"x": 40, "y": 80, "zoom": 0.6},
    })


def main():
    print("\n╔══════════════════════════════════════╗")
    print("║  CODEFORGE → Flowise Cloud Setup     ║")
    print("╚══════════════════════════════════════╝\n")

    print("Removing old CODEFORGE flows...")
    delete_existing("CODEFORGE — Multi-Agent Pipeline")

    print("Building agentflow JSON...")
    flow_data = build_flow()

    print("Creating flow in Flowise Cloud...")
    result = api("POST", "/api/v1/chatflows", {
        "name": "CODEFORGE — Multi-Agent Pipeline",
        "flowData": flow_data,
        "deployed": True,
        "type": "MULTIAGENT",
        "category": "Code Generation",
    })

    flow_id = result["id"]
    print(f"\n✅ Flow Created Successfully!")
    print(f"   Flow ID : {flow_id}")
    print(f"   Name    : {result['name']}")
    print(f"   Status  : Deployed")
    print(f"\n🌐 Canvas URL : {FLOWISE_URL}/canvas/{flow_id}")
    print(f"📡 API URL    : {FLOWISE_URL}/api/v1/prediction/{flow_id}")

    print("\n" + "─"*55)
    print("⚠️  ONE MANUAL STEP REQUIRED IN FLOWISE UI:")
    print("─"*55)
    print("  1. Open Flowise → canvas above URL")
    print("  2. Click the '⚡ ChatGroq' node (bottom of canvas)")
    print("  3. Click 'Connect Credential' → Add New")
    print("  4. Enter your Groq API key:")
    print(f"     {GROQ_API_KEY[:8]}...{GROQ_API_KEY[-4:]}  (from your .env)")
    print("  5. Save → all 5 LLM agents will use it automatically")
    print("─"*55)
    print("\nAll 8 nodes created:")
    print("  ▶ START → 🎯 ORCHESTRATOR → 📋 PLANNER → 💻 CODER")
    print("  → 🔍 REVIEWER → ❓ CONDITION → ⚡ EXECUTOR / 🐛 DEBUGGER")
    print("  → ✅ DONE\n")


if __name__ == "__main__":
    main()
