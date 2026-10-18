"""
agent.py — the LLM decides WHICH tool to call and WITH WHAT arguments.
Our code does the actual calling via MCP.

Uses OpenAI with an API key loaded from the environment or a local `.env` file.

Usage:
  python agent.py "What is the score in India vs West Indies?"
  python agent.py --no-tools "What is the score in India vs West Indies?"
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from openai import OpenAI

# Load OPENAI_API_KEY from a .env file sitting next to this script (keeps the key off your screen).
# If python-dotenv isn't installed (e.g. in Colab), we simply skip this and use the environment.
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).with_name(".env"))
except ImportError:
    pass
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
# Start cricket_server.py (found next to this script) with the same Python that runs this script
server = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("cricket_server.py"))])


def to_openai_format(mcp_tools):
    """MCP tool list -> the format OpenAI's API expects."""
    return [{
        "type": "function",
        "function": {"name": t.name, "description": t.description or "", "parameters": t.inputSchema},
    } for t in mcp_tools]


def call_llm(llm, kwargs, retries=2):
    """Call the model. Returns (message, None) or (None, error_text).

    Retry transient API failures before returning a readable error to the caller.
    """
    last = None
    for _ in range(retries + 1):
        try:
            return llm.chat.completions.create(**kwargs).choices[0].message, None
        except Exception as e:
            last = str(e)
    return None, f"API ERROR: {last}"


async def run_agent(question: str, use_tools: bool = True, verbose: bool = True) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY is not set. Put it in a .env file next to this script "
                 "(OPENAI_API_KEY=sk-...).")
    llm = OpenAI(api_key=api_key)
    trace = []  # every tool call the LLM asked for, kept for evals later
    if use_tools:
        system = ("You are a cricket assistant. Use ONLY the functions provided to get live data. "
                  "Do not use any browser or code tools. Be brief.")
    else:
        system = ("You are a cricket assistant. You have NO tools, NO browser and NO internet access. "
                  "Never try to call a tool. Answer only from your own knowledge, in 1-2 sentences.")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = to_openai_format((await session.list_tools()).tools) if use_tools else None

            for _ in range(5):  # safety limit on loop turns
                kwargs = {"model": MODEL, "messages": messages, "temperature": 0}
                if tools:
                    kwargs["tools"] = tools
                reply, error = call_llm(llm, kwargs)
                if error:
                    if verbose:
                        print(f"\n{error}")
                    return {"answer": f"({error})", "trace": trace}

                if not reply.tool_calls:  # LLM gave a final answer
                    if verbose:
                        print(f"\nFINAL ANSWER: {reply.content}")
                    return {"answer": reply.content, "trace": trace}

                # Record the LLM's "prescription" in the conversation (plain dict = works with any provider)
                messages.append({
                    "role": "assistant",
                    "content": reply.content or "",
                    "tool_calls": [{"id": c.id, "type": "function",
                                    "function": {"name": c.function.name, "arguments": c.function.arguments}}
                                   for c in reply.tool_calls],
                })
                for call in reply.tool_calls:
                    args = json.loads(call.function.arguments)
                    trace.append({"tool": call.function.name, "args": args})
                    if verbose:
                        print(f"\nLLM SAYS: please call {call.function.name} with {args}")
                    result = await session.call_tool(call.function.name, args)  # OUR code calls the tool
                    text = result.content[0].text if result.content else "(empty)"
                    if verbose:
                        print(f"TOOL RETURNED: {text}")
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": text})

    return {"answer": "(stopped: too many steps)", "trace": trace}


if __name__ == "__main__":
    args = sys.argv[1:]
    use_tools = "--no-tools" not in args
    question = " ".join(a for a in args if a != "--no-tools") or "What is the score in India vs West Indies?"
    print(f"QUESTION: {question}   (tools {'ON' if use_tools else 'OFF'})")
    asyncio.run(run_agent(question, use_tools))
