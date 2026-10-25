"""Coordinator for the finance research specialist agents."""

import sys
from pathlib import Path

from agents import Agent

AGENTS_DIR = Path(__file__).resolve().parent
if str(AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AGENTS_DIR))

from finacial_data_agent import financial_data_agent
from news_sentiment_agent import news_sentiment_agent
from report_writer_agent import report_writer_agent
from risk_agent import risk_agent
from valuation_agent import valuation_agent


orchestrator = Agent(
    name="finance_research_orchestrator",
    instructions="""You coordinate a company research workflow.
Delegate each question to the appropriate specialist:
- financial_data_analyst: reported financial statements and operating metrics
- valuation_analyst: market multiples and valuation context
- news_sentiment_analyst: recent company news and market context
- risk_analyst: business, financial, valuation, and execution risks
- report_writer: final integrated earnings or company report

For a full company or earnings report, gather the specialist analyses first,
then ask report_writer to synthesize them. Do not invent data, and make clear
when a provider or API key cannot supply requested information. The final
output is educational research, not personalized investment advice.""",
    tools=[
    financial_data_agent.as_tool(
        "financial_data_analyst",
        "Analyze the company's financial statements and operating metrics.",
    ),
    valuation_agent.as_tool(
        "valuation_analyst",
        "Analyze the company's valuation metrics and market multiples.",
    ),
    news_sentiment_agent.as_tool(
        "news_sentiment_analyst",
        "Analyze recent company news and market context.",
    ),
    risk_agent.as_tool(
        "risk_analyst",
        "Analyze business, financial, valuation, and execution risks.",
    ),
    report_writer_agent.as_tool(
        "report_writer",
        "Synthesize specialist analyses into an integrated company report.",
    ),
],
)