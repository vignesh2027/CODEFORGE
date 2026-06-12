#!/usr/bin/env python3
"""
Creates the CODEFORGE agent in Flowise Cloud.
Uses ChatGroq with API key embedded directly — no credential panel needed.
Tavily omitted from Flowise (Flowise Cloud blocks credential API; web search
runs in the full LangGraph pipeline instead).
Run: python3 flowise/create_flow.py
"""
import json, os, requests
from typing import Any
from dotenv import load_dotenv

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root, ".env"))

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

FLOWISE_URL = "https://cloud.flowiseai.com"
FLOWISE_KEY = "BkV4qapsZW6FUoVHdASgmcyEeaRyUy9XkFYqYjKFQ8U"
HEADERS = {"Authorization": f"Bearer {FLOWISE_KEY}", "Content-Type": "application/json"}


def api(method: str, path: str, body: Any = None) -> Any:
    url = f"{FLOWISE_URL}{path}"
    fn = {"GET": requests.get, "POST": requests.post,
          "PUT": requests.put, "DELETE": requests.delete}[method]
    r = fn(url, headers=HEADERS, json=body, timeout=20)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"{method} {path} → {r.status_code}: {r.text[:400]}")
    data: Any = r.json()
    return data


def delete_all_codeforge() -> None:
    flows: list[Any] = api("GET", "/api/v1/chatflows") or []
    for f in flows:
        if "CODEFORGE" in f.get("name", ""):
            try:
                api("DELETE", f"/api/v1/chatflows/{f['id']}")
                print(f"  Deleted: {f['name']}")
            except Exception:
                pass


SYSTEM_PROMPT = """You are CODEFORGE — an expert AI code generation system.

When the user gives you a coding task, follow this pipeline:

**STEP 1 — ANALYZE**
Identify the programming language (default Python). State: "Language: [LANG]"

**STEP 2 — PLAN**
Create a numbered step-by-step implementation plan covering:
- Required functions / classes
- Libraries needed
- Edge cases and error handling

**STEP 3 — CODE**
Write COMPLETE, production-quality code:
- No pseudocode, no placeholders
- Full error handling
- Wrapped in ```language code blocks

**STEP 4 — REVIEW**
Self-review: correctness, completeness, quality (score 1-10).
Rewrite if score < 7.

**STEP 5 — EXPLAIN**
Brief explanation: what it does, how to run it, expected output.

Always produce working, tested code."""


def build_chatflow():
    """
    Two-node CHATFLOW:
      [ChatGroq] → [CODEFORGE Agent]
    Groq API key embedded directly in node inputs (Flowise Cloud credential API is restricted).
    """

    groq_node = {
        "id": "groqChat_0",
        "position": {"x": 200, "y": 200},
        "type": "customNode",
        "data": {
            "id": "groqChat_0",
            "label": "ChatGroq",
            "name": "groqChat",
            "version": 6,
            "type": "ChatGroq",
            "category": "Chat Models",
            "baseClasses": ["GroqChat", "BaseChatModel", "BaseLanguageModel", "Runnable"],
            "inputs": {
                "groqApiKey": GROQ_API_KEY,
                "modelName": "llama-3.3-70b-versatile",
                "temperature": 0.1,
                "streaming": True,
                "maxTokens": 4096,
            },
            "inputParams": [
                {"label": "Groq API Key", "name": "groqApiKey",
                 "type": "password", "placeholder": "gsk_..."},
                {"label": "Model Name",   "name": "modelName",   "type": "string",
                 "default": "llama-3.3-70b-versatile"},
                {"label": "Temperature",  "name": "temperature",  "type": "number", "default": 0.1},
                {"label": "Max Tokens",   "name": "maxTokens",    "type": "number", "optional": True},
                {"label": "Streaming",    "name": "streaming",    "type": "boolean", "default": True},
            ],
            "inputAnchors": [
                {"label": "Cache", "name": "cache", "type": "BaseCache",
                 "optional": True, "id": "groqChat_0-input-cache-BaseCache"}
            ],
            "outputAnchors": [
                {
                    "name": "output",
                    "label": "ChatGroq",
                    "type": "options",
                    "options": [
                        {
                            "id": "groqChat_0-output-ChatGroq-GroqChat-BaseChatModel-BaseLanguageModel-Runnable",
                            "name": "output",
                            "label": "ChatGroq",
                            "type": "GroqChat | BaseChatModel | BaseLanguageModel | Runnable"
                        }
                    ],
                    "default": "groqChat_0-output-ChatGroq-GroqChat-BaseChatModel-BaseLanguageModel-Runnable"
                }
            ],
            "outputs": {},
            "selected": False,
        },
        "width": 300, "height": 420, "selected": False,
    }

    memory_node = {
        "id": "bufferMemory_0",
        "position": {"x": 200, "y": 680},
        "type": "customNode",
        "data": {
            "id": "bufferMemory_0",
            "label": "Buffer Memory",
            "name": "bufferMemory",
            "version": 2,
            "type": "BufferMemory",
            "category": "Memory",
            "baseClasses": ["BufferMemory", "BaseChatMemory", "BaseMemory"],
            "inputs": {
                "memoryKey": "chat_history",
                "inputKey": "input",
                "returnMessages": True,
            },
            "inputParams": [
                {"label": "Memory Key",  "name": "memoryKey",      "type": "string",  "default": "chat_history"},
                {"label": "Input Key",   "name": "inputKey",        "type": "string",  "default": "input"},
                {"label": "Return Messages", "name": "returnMessages", "type": "boolean", "default": True},
            ],
            "inputAnchors": [],
            "outputAnchors": [
                {
                    "name": "output",
                    "label": "BufferMemory",
                    "type": "options",
                    "options": [
                        {"id": "bufferMemory_0-output-BufferMemory-BufferMemory-BaseChatMemory-BaseMemory",
                         "name": "output", "label": "BufferMemory",
                         "type": "BufferMemory | BaseChatMemory | BaseMemory"}
                    ],
                    "default": "bufferMemory_0-output-BufferMemory-BufferMemory-BaseChatMemory-BaseMemory"
                }
            ],
            "outputs": {},
            "selected": False,
        },
        "width": 300, "height": 300, "selected": False,
    }

    agent_node = {
        "id": "toolAgent_0",
        "position": {"x": 620, "y": 200},
        "type": "customNode",
        "data": {
            "id": "toolAgent_0",
            "label": "CODEFORGE Agent",
            "name": "toolAgent",
            "version": 2,
            "type": "AgentExecutor",
            "category": "Agents",
            "baseClasses": ["AgentExecutor", "BaseChain", "Runnable"],
            "inputs": {
                "model": "{{groqChat_0.data.instance}}",
                "memory": "{{bufferMemory_0.data.instance}}",
                "tools": [],
                "systemMessage": SYSTEM_PROMPT,
                "maxIterations": 10,
            },
            "inputParams": [
                {"label": "System Message", "name": "systemMessage", "type": "string",
                 "rows": 4, "optional": True, "additionalParams": True},
                {"label": "Max Iterations", "name": "maxIterations", "type": "number",
                 "optional": True, "additionalParams": True, "default": 10},
            ],
            "inputAnchors": [
                {"label": "Tools",      "name": "tools",  "type": "Tool",          "list": True,
                 "id": "toolAgent_0-input-tools-Tool"},
                {"label": "Memory",     "name": "memory", "type": "BaseChatMemory", "optional": True,
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
        "width": 300, "height": 440, "selected": False,
    }

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
            "id": "e-mem-agent",
            "source": "bufferMemory_0",
            "target": "toolAgent_0",
            "sourceHandle": "bufferMemory_0-output-BufferMemory-BufferMemory-BaseChatMemory-BaseMemory",
            "targetHandle": "toolAgent_0-input-memory-BaseChatMemory",
            "type": "buttonedge",
            "animated": False,
        },
    ]

    return json.dumps({
        "nodes": [groq_node, memory_node, agent_node],
        "edges": edges,
        "viewport": {"x": 60, "y": 40, "zoom": 0.9},
    })


def test_flow(flow_id):
    print("\nTesting prediction endpoint...")
    r = requests.post(
        f"{FLOWISE_URL}/api/v1/prediction/{flow_id}",
        headers={**HEADERS},
        json={"question": "Write a Python one-liner to reverse a string."},
        timeout=60
    )
    if r.status_code == 200:
        data = r.json()
        text = data.get("text", data.get("output", str(data)))
        print(f"  ✅ API works! Response preview: {text[:150]}...")
    else:
        print(f"  ❌ Status {r.status_code}: {r.text[:300]}")


def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║  CODEFORGE → Flowise  (Groq key embedded)   ║")
    print("╚══════════════════════════════════════════════╝\n")

    print("Step 1: Removing old CODEFORGE flows...")
    delete_all_codeforge()

    print("Step 2: Creating ChatGroq + Agent flow...")
    flow_data = build_chatflow()
    result = api("POST", "/api/v1/chatflows", {
        "name": "CODEFORGE — Code Generation Agent",
        "flowData": flow_data,
        "deployed": True,
        "type": "CHATFLOW",
        "category": "Code Generation",
    })

    flow_id = result["id"]
    print(f"  Created: {flow_id}")

    test_flow(flow_id)

    print(f"\n✅ CODEFORGE Flowise flow is live and working!")
    print(f"\n🌐 Canvas : {FLOWISE_URL}/canvas/{flow_id}")
    print(f"📡 API    : {FLOWISE_URL}/api/v1/prediction/{flow_id}")
    print()


if __name__ == "__main__":
    main()
