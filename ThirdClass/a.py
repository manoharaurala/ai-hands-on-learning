import os

import langchain
from langchain.agents import create_agent

from util.config import get_api_key

print("LangChain version:", langchain.__version__)

# ---------------------------------------------------------------------------
# Pick your provider here.
# ---------------------------------------------------------------------------
# "groq"   -> free + fast.  Key: https://console.groq.com      (GROQ_API_KEY)
# "gemini" -> free tier.    Key: https://aistudio.google.com   (GOOGLE_API_KEY)
# "openai" -> needs billing/credits set up.                    (OPENAI_API_KEY)
PROVIDER = "openai"  # "groq" | "gemini" | "openai"

if PROVIDER == "groq":
    MODEL = "groq:llama-3.3-70b-versatile"  # check console.groq.com for current IDs
    REQUIRED_KEY = "GROQ_API_KEY"
elif PROVIDER == "gemini":
    MODEL = "google_genai:gemini-3.6-flash"
    REQUIRED_KEY = "GOOGLE_API_KEY"
else:  # openai
    MODEL = "openai:gpt-4o-mini"
    REQUIRED_KEY = "OPENAI_API_KEY"

os.environ.setdefault(REQUIRED_KEY, get_api_key(REQUIRED_KEY))

print(f"Provider: {PROVIDER}")
print(f"Model: {MODEL}")

# ---------------------------------------------------------------------------
# Tools
#   1. Type hints (city: str)  -> tell the model what arguments to pass
#   2. The docstring           -> tells the model WHEN to use this tool
# ---------------------------------------------------------------------------

def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    return f"The weather in {city} is sunny, 28 degrees C."


def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


def get_population(city: str) -> str:
    """Get the approximate population of a major city."""
    data = {
        "new york": "8.5 million",
        "london": "9 million",
        "bangalore": "13 million",
        "tokyo": "14 million",
    }
    return data.get(city.lower(), f"Sorry, I don't have population data for {city}.")


TOOLS = [get_weather, add, multiply, get_population]

# ---------------------------------------------------------------------------
# Build the agent
# ---------------------------------------------------------------------------
agent = create_agent(
    model=MODEL,
    tools=TOOLS,
    # Tighter prompt: force the model to actually state the result so we don't
    # get vague answers like "that's the current weather".
    system_prompt=(
        "You are a helpful assistant. Use the available tools when needed. "
        "Always state the final result clearly and completely in your answer."
    ),
)


# ---------------------------------------------------------------------------
# Run a question and (optionally) show every tool call + tool result.
# ---------------------------------------------------------------------------
def ask(question: str, show_steps: bool = True) -> None:
    response = agent.invoke({"messages": [{"role": "user", "content": question}]})
    print(f"\nQ: {question}")

    if show_steps:
        for msg in response["messages"]:
            # The AI decided to call one or more tools
            if msg.type == "ai" and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    print(f"   [tool call]   {tc['name']}({tc['args']})")
            # A tool returned its result
            elif msg.type == "tool":
                print(f"   [tool result] {msg.content}")

    print(f"A: {response['messages'][-1].content}")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    ask("What is the weather like in New York?")          # -> get_weather
    ask("What is 25 multiplied by 4?")                     # -> multiply
    ask("What is 137 plus 568?")                           # -> add
    ask("What is the population of Bangalore?")            # -> get_population
    ask("What's the weather in Tokyo, and what is 12 times 12?")  # -> two tools
    ask("Who wrote the play Romeo and Juliet?")   # -> no tool needed