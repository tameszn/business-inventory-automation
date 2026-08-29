"""
The agent loop. This is the entire "intelligence" of the assistant:
call the model, execute whatever tools it asks for, feed results back,
repeat until it returns a plain-text answer.
"""
import json
import os


from openai import OpenAI

from app.tool_schemas import TOOL_SCHEMAS
from app.tools import TOOL_MAP
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = os.environ.get("AGENT_MODEL", "gemini-2.5-flash")

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

SYSTEM_PROMPT = """You are a personal productivity assistant for a small business owner.
You help them check sales, monitor inventory, and understand product performance —
using only the tools available to you. Never invent numbers; always call a tool to
get real data before answering a factual question.

When a request would change data (like updating stock), first call the relevant tool
with confirm=false, clearly relay the confirmation message to the owner in your own words,
and wait for their explicit yes before calling it again with confirm=true.

Keep answers short and concrete — the owner is checking this between other tasks, not
reading a report. Use rupee amounts as plain numbers (e.g. "₹4,250"). If asked something
outside what your tools can do, say so plainly rather than guessing.
"""


def run_agent(messages: list, max_turns: int = 6) -> str:
    """
    messages: full conversation history (list of role/content dicts), including
    the system prompt. Mutated in place — tool calls and results are appended
    so the caller's session store stays in sync.
    """
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return msg.content or ""

        for call in msg.tool_calls:
            fn = TOOL_MAP.get(call.function.name)
            try:
                args = json.loads(call.function.arguments or "{}")
                result = fn(**args) if fn else {"error": f"Unknown tool '{call.function.name}'"}
            except Exception as e:
                result = {"error": str(e)}

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    return "I wasn't able to finish that in time — try asking in a simpler or more specific way."
