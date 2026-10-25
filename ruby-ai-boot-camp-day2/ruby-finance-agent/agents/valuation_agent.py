"""Valuation specialist agent."""

from agents import Agent

from tools.valuation_tools import get_company_valuation


valuation_agent = Agent(
    name="valuation_analyst",
    instructions="""You are a valuation analyst.
Use get_company_valuation to retrieve current market multiples and valuation
metrics. Explain what each important metric means, compare valuation with
reasonable industry context when available, and separate reported figures
from your interpretation. Never invent missing data or provide personalized
investment advice.""",
    tools=[get_company_valuation],
)