"""Module 2 · Lesson 5 — Pre-built community tools.

You don't have to write everything. strands_tools ships ready-made tools.
This also introduces the SYSTEM PROMPT: standing instructions that shape
the agent's behaviour on every request.

    python project2/05_prebuilt_tools.py
"""
from config import NOVA_LITE
from strands import Agent
from strands.models import BedrockModel
from strands_tools import calculator

llm = BedrockModel(model_id=NOVA_LITE)
agent = Agent(
    model=llm,
    tools=[calculator],
    system_prompt="You are a helpful math assistant."
)

agent("What's 42 raised to the power of 9?")
agent("Solve the equation x^2 + 5x + 6 = 0")
agent("What's the derivative of sin(x) * cos(x)?")
