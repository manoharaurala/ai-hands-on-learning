"""Financial-statement specialist agent."""

from agents import Agent

from tools.financial_tools import get_company_financials


financial_data_agent = Agent(
    name="financial_data_analyst",
    instructions="""You are a financial-statement analyst.
Use get_company_financials to review revenue, earnings, margins, cash flow,
assets, liabilities, equity, leverage, and return metrics. Highlight trends,
strengths, weaknesses, and missing data. Report the figures as provided and
do not give personalized investment advice.""",
    tools=[get_company_financials],
)