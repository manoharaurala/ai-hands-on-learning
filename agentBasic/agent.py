import json

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

PRICES = {"shoes": 799, "hat": 399, "bag": 1420, "shorts": 1299, "pants": 1699}


def get_price(item):
    print(f"🔧 tool called: get_price({item})")
    return f"₹{PRICES.get(item.lower(), 'unknown')}"


tools = [
    {
        "type": "function",  # ①
        "function": {
            "name": "get_price",  # ②
            "description": "Get the price of a shop item the user asks about.",  # ③
            "parameters": {  # ④
                "type": "object",
                "properties": {
                    "item": {
                        "type": "string",
                        "description": "The item name, such as shoes, hat, or bag.",
                    }
                },
                "required": ["item"],
                "additionalProperties": False,
            },
        },
    }
]


def _history_messages(history):
    messages = []
    for turn in history or []:
        if isinstance(turn, dict):
            role = turn.get("role")
            content = turn.get("content")
            if role in {"user", "assistant"} and isinstance(content, str) and content:
                messages.append({"role": role, "content": content})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            user_text, assistant_text = turn
            if isinstance(user_text, str) and user_text:
                messages.append({"role": "user", "content": user_text})
            if isinstance(assistant_text, str) and assistant_text:
                messages.append({"role": "assistant", "content": assistant_text})
    return messages


def agent(user_message, history=None):
    messages = _history_messages(history)

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(  # ① send message + tools menu
        model="gpt-4o-mini", messages=messages, tools=tools)
    msg = response.choices[0].message

    if msg.tool_calls:  # ② did it ask for a tool?
        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in msg.tool_calls
                ],
            }
        )
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)  # ③ read its request, run it
            result = get_price(args["item"])
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                }
            )
        response = client.chat.completions.create(  # ④ send it all back → nice answer
            model="gpt-4o-mini", messages=messages)
        msg = response.choices[0].message

    return msg.content or ""


if __name__ == "__main__":
    print(agent("How much are the shoes?"))  # → tool fires → "₹799"
    print(agent("Hi! What can you help with?"))  # → no tool → just chats
