"""Coordinator for the staged finance research workflow."""

import asyncio
import sys
from pathlib import Path

from agents import Agent, Runner

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
    instructions="""Coordinate company research in stages:
1. Run financial-data, news-sentiment, and risk analysis concurrently.
2. Send the financial-data analysis to the valuation analyst.
3. Send all four analyses to the report writer for the final investment brief.
Do not invent data. The output is educational research, not personalized
investment advice.""",
)


async def _run_specialist(agent: Agent, request: str) -> str:
    result = await Runner.run(agent, request)
    return result.final_output


async def run_research_workflow(request: str) -> str:
    """Run the staged workflow with explicit dependencies between agents."""
    financial_analysis, news_analysis, risk_analysis = await asyncio.gather(
        _run_specialist(
            financial_data_agent,
            f"""Analyze the company in this request. Return financial
statements, earnings-call commentary, guidance, and operating trends.

Request: {request}""",
        ),
        _run_specialist(
            news_sentiment_agent,
            f"""Analyze recent news, catalysts, and market sentiment for the
company in this request. Separate reported facts from interpretation.

Request: {request}""",
        ),
        _run_specialist(
            risk_agent,
            f"""Analyze business, financial, valuation, execution, regulatory,
competitive, and market risks for the company in this request.

Request: {request}""",
        ),
    )

    valuation_analysis = await _run_specialist(
        valuation_agent,
        f"""Analyze valuation for this request. Use the financial-data analysis
as context for interpreting multiples, growth, profitability, and balance
sheet quality. Do not invent missing figures.

Request: {request}

Financial-data analysis:
{financial_analysis}""",
    )

    return await _run_specialist(
        report_writer_agent,
        f"""Write the final company research report and investment brief using
the specialist analyses below. Reconcile conflicts and label uncertainty.

Request:
{request}

Financial-data analysis:
{financial_analysis}

News and sentiment analysis:
{news_analysis}

Risk analysis:
{risk_analysis}

Valuation analysis:
{valuation_analysis}""",
    )
