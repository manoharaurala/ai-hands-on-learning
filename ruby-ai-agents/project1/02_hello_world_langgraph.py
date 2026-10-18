"""Module 1 · Lesson 2 — Same idea in LangGraph, WITH a tool.

Strands isn't the only framework. This uses LangGraph and adds a small tool,
so you can watch the agentic loop actually loop.

WHAT TO LOOK FOR in the output:
    human: Please greet Ruby  and Annayya.
    ai:                                  <-- EMPTY! the model chose to use a tool
    tool: Hello, Ruby! ...              <-- the tool ran
    tool: Hello, Annayya! ...                <-- and ran again
    ai: Done! I've greeted both...       <-- now it answers

That empty `ai:` line is the model deciding to act instead of replying.
That IS the agentic loop.

    python project1/02_hello_world_langgraph.py
"""

from config import MODEL_ID
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent


# Define a simple tool

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome to the world of AI agents."


# Initialize the LLM via Bedrock

llm = init_chat_model(
    model=MODEL_ID,
    model_provider="bedrock_converse"
)

# Create a ReAct agent with the tool

agent = create_react_agent(
    model=llm,
    tools=[greet],
)

# Run the agent
response = agent.invoke(
    {"messages": [{"role": "user", "content": "Please greet Ruby and Annayya."}]}
)

# Print every step so you can see the loop
for message in response["messages"]:
    print(f"{message.type}: {message.text}")
