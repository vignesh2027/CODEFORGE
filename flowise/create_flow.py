#!/usr/bin/env python3
"""
Creates the CODEFORGE agent in Flowise Cloud as a proper CHATFLOW.
Nodes are connected with real edges — no template strings.
Run: python3 flowise/create_flow.py
"""
import json, sys, os, requests
from dotenv import load_dotenv

# Load .env from the project root (one level up from flowise/)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root, ".env"))

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

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


def delete_all_codeforge():
    flows = api("GET", "/api/v1/chatflows")
    for f in flows:
        if "CODEFORGE" in f.get("name", ""):
            try:
                api("DELETE", f"/api/v1/chatflows/{f['id']}")
                print(f"  Deleted: {f['name']}")
            except Exception:
                pass


CODEFORGE_SYSTEM_PROMPT = """You are CODEFORGE — an expert AI code generation system.

When the user gives you a coding task, follow this exact pipeline:

**STEP 1 — ANALYZE**
Identify the programming language (default Python). State: "Language: [LANG]"

**STEP 2 — PLAN**
Create a numbered step-by-step implementation plan. Cover:
- Required functions and classes
- Libraries needed
- Error handling and edge cases

**STEP 3 — CODE**
Write COMPLETE, production-quality code. Rules:
- No pseudocode, no placeholders
- Full error handling included
- Wrap in ```language code block
- Use web search (Tavily) if you need to look up APIs or libraries

**STEP 4 — REVIEW**
Self-review your code:
- Correctness: does it solve the task?
- Completeness: is it runnable right now?
- Quality: clean and idiomatic?
Score it 1-10. If score < 7, rewrite before showing.

**STEP 5 — EXPLAIN**
After the code, briefly explain:
- What it does
- How to run it
- Expected output

Always produce working, tested code. Use Tavily search when you need current documentation."""


def build_chatflow():
    """
    Proper Flowise CHATFLOW with real node-to-node edge connections.

    Layout:
      [ChatGroq]  [TavilySearch]
          ↘           ↙
           [Tool Agent]
    """

    # ── Node: ChatGroq ─────────────────────────────────────────────────────
    groq_node = {
        "id": "groqChat_0",
        "position": {"x": 200, "y": 100},
        "type": "customNode",
        "data": {
            "id": "groqChat_0",
            "label": "ChatGroq",
            "name": "groqChat",
            "version": 6,
            "type": "ChatGroq",
            "category": "Chat Models",
            "description": "Wrapper around Groq API with tool calling support",
            "baseClasses": ["GroqChat", "BaseChatModel", "BaseLanguageModel", "Runnable"],
            "inputs": {
                "modelName": "llama-3.3-70b-versatile",
                "temperature": 0.1,
                "streaming": True,
                "maxTokens": 4096,
            },
            "inputParams": [
                {"label": "Model Name",  "name": "modelName", "type": "asyncOptions",
                 "loadMethod": "listModels", "default": "llama3-8b-8192"},
                {"label": "Temperature", "name": "temperature", "type": "number", "default": 0.9},
                {"label": "Max Tokens",  "name": "maxTokens", "type": "number", "optional": True},
                {"label": "Streaming",   "name": "streaming", "type": "boolean", "default": True},
            ],
            "inputAnchors": [
                {"label": "Cache", "name": "cache", "type": "BaseCache", "optional": True, "id": "groqChat_0-input-cache-BaseCache"}
            ],
            "outputAnchors": [
                {
                    "name": "output",
                    "label": "ChatGroq",
                    "type": "options",
                    "options": [
                        {"id": "groqChat_0-output-ChatGroq-GroqChat-BaseChatModel-BaseLanguageModel-Runnable",
                         "name": "output", "label": "ChatGroq",
                         "description": "Generated output from model",
                         "type": "GroqChat | BaseChatModel | BaseLanguageModel | Runnable"}
                    ],
                    "default": "groqChat_0-output-ChatGroq-GroqChat-BaseChatModel-BaseLanguageModel-Runnable"
                }
            ],
            "outputs": {},
            "selected": False,
        },
        "width": 300, "height": 380, "selected": False,
    }

    # ── Node: Tavily Search ────────────────────────────────────────────────
    tavily_node = {
        "id": "tavilyAPI_0",
        "position": {"x": 600, "y": 100},
        "type": "customNode",
        "data": {
            "id": "tavilyAPI_0",
            "label": "Tavily Search",
            "name": "tavilyAPI",
            "version": 1,
            "type": "TavilyAPI",
            "category": "Tools",
            "description": "Real-time web search via Tavily API",
            "baseClasses": ["TavilyAPI", "StructuredTool", "BaseTool", "Runnable"],
            "inputs": {
                "maxResults": 5,
                "searchDepth": "basic",
                "topic": "general",
                "includeAnswer": False,
            },
            "inputParams": [
                {"label": "Max Results",   "name": "maxResults",   "type": "number",  "default": 5},
                {"label": "Search Depth",  "name": "searchDepth",  "type": "options",
                 "options": [{"label": "Basic", "name": "basic"}, {"label": "Advanced", "name": "advanced"}],
                 "default": "basic"},
                {"label": "Topic",         "name": "topic",         "type": "options",
                 "options": [{"label": "General", "name": "general"}, {"label": "News", "name": "news"}],
                 "default": "general"},
            ],
            "inputAnchors": [],
            "outputAnchors": [
                {
                    "name": "output",
                    "label": "TavilyAPI",
                    "type": "options",
                    "options": [
                        {"id": "tavilyAPI_0-output-TavilyAPI-TavilyAPI-StructuredTool-BaseTool-Runnable",
                         "name": "output", "label": "TavilyAPI",
                         "type": "TavilyAPI | StructuredTool | BaseTool | Runnable"}
                    ],
                    "default": "tavilyAPI_0-output-TavilyAPI-TavilyAPI-StructuredTool-BaseTool-Runnable"
                }
            ],
            "outputs": {},
            "selected": False,
        },
        "width": 300, "height": 380, "selected": False,
    }

    # ── Node: Tool Agent ───────────────────────────────────────────────────
    agent_node = {
        "id": "toolAgent_0",
        "position": {"x": 400, "y": 600},
        "type": "customNode",
        "data": {
            "id": "toolAgent_0",
            "label": "CODEFORGE Agent",
            "name": "toolAgent",
            "version": 2,
            "type": "AgentExecutor",
            "category": "Agents",
            "description": "CODEFORGE multi-step code generation agent",
            "baseClasses": ["AgentExecutor", "BaseChain", "Runnable"],
            "inputs": {
                "model": "{{groqChat_0.data.instance}}",
                "tools": ["{{tavilyAPI_0.data.instance}}"],
                "systemMessage": CODEFORGE_SYSTEM_PROMPT,
                "maxIterations": 10,
                "enableDetailedStreaming": False,
            },
            "inputParams": [
                {"label": "System Message", "name": "systemMessage", "type": "string",
                 "rows": 4, "optional": True,
                 "additionalParams": True, "default": ""},
                {"label": "Max Iterations", "name": "maxIterations", "type": "number",
                 "optional": True, "additionalParams": True, "default": 10},
            ],
            "inputAnchors": [
                {"label": "Tools",      "name": "tools",  "type": "Tool",         "list": True,
                 "id": "toolAgent_0-input-tools-Tool"},
                {"label": "Memory",     "name": "memory", "type": "BaseChatMemory","optional": True,
                 "id": "toolAgent_0-input-memory-BaseChatMemory"},
                {"label": "Chat Model", "name": "model",  "type": "BaseChatModel",
                 "id": "toolAgent_0-input-model-BaseChatModel"},
                {"label": "Chat Prompt Template", "name": "chatPromptTemplate",
                 "type": "ChatPromptTemplate", "optional": True,
                 "id": "toolAgent_0-input-chatPromptTemplate-ChatPromptTemplate"},
            ],
            "outputAnchors": [
                {"id": "toolAgent_0-output-toolAgent-AgentExecutor-BaseChain-Runnable",
                 "name": "output", "label": "AgentExecutor",
                 "type": "AgentExecutor | BaseChain | Runnable"}
            ],
            "outputs": {},
            "selected": False,
        },
        "width": 300, "height": 430, "selected": False,
    }

    # ── Edges: real node-to-node connections ────────────────────────────────
    edges = [
        {
            "id": "e-groq-agent",
            "source": "groqChat_0",
            "target": "toolAgent_0",
            "sourceHandle": "groqChat_0-output-ChatGroq-GroqChat-BaseChatModel-BaseLanguageModel-Runnable",
            "targetHandle": "toolAgent_0-input-model-BaseChatModel",
            "type": "buttonedge",
            "animated": True,
        },
        {
            "id": "e-tavily-agent",
            "source": "tavilyAPI_0",
            "target": "toolAgent_0",
            "sourceHandle": "tavilyAPI_0-output-TavilyAPI-TavilyAPI-StructuredTool-BaseTool-Runnable",
            "targetHandle": "toolAgent_0-input-tools-Tool",
            "type": "buttonedge",
            "animated": True,
        },
    ]

    return json.dumps({
        "nodes": [groq_node, tavily_node, agent_node],
        "edges": edges,
        "viewport": {"x": 80, "y": 40, "zoom": 0.9},
    })


def main():
    print("\n╔════════════════════════════════════════╗")
    print("║  CODEFORGE → Flowise  (Proper Build)  ║")
    print("╚════════════════════════════════════════╝\n")

    print("Removing all old CODEFORGE flows...")
    delete_all_codeforge()

    print("Creating proper CHATFLOW with real edge connections...")
    flow_data = build_chatflow()
    result = api("POST", "/api/v1/chatflows", {
        "name": "CODEFORGE — Code Generation Agent",
        "flowData": flow_data,
        "deployed": True,
        "type": "CHATFLOW",
        "category": "Code Generation",
    })

    flow_id = result["id"]
    print(f"\n✅ Flow Created!")
    print(f"   ID   : {flow_id}")
    print(f"   Type : CHATFLOW (3 nodes, 2 edges)")
    print(f"\n🌐 Open now: {FLOWISE_URL}/canvas/{flow_id}")
    print(f"📡 API URL : {FLOWISE_URL}/api/v1/prediction/{flow_id}")

    print("\n" + "─"*55)
    print("⚠️  ONE STEP IN FLOWISE UI (takes 20 seconds):")
    print("─"*55)
    print()
    print("  1. Open the canvas URL above")
    print("  2. You will see 3 nodes:")
    print("     [ChatGroq] ──→ [CODEFORGE Agent] ←── [Tavily Search]")
    print()
    print("  3. Click the [ChatGroq] node")
    print("  4. In the right panel → 'Connect Credential' dropdown")
    print("  5. Click '+ Add New Credential'")
    print("  6. Name: Groq  |  API Key: your Groq key")
    print("  7. Click Save")
    print("  8. Click [Save] button (top right of canvas)")
    print()
    print("  That's it — the flow will be fully working!")
    print("─"*55)
    print(f"\nTavily key for node config: {TAVILY_API_KEY[:12]}...")
    print()


if __name__ == "__main__":
    main()
