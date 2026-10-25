"""Risk-analysis specialist agent."""

from agents import Agent

from tools.financial_tools import get_company_financials, get_earnings_transcript
from tools.news_tools import get_financial_news
from tools.valuation_tools import get_company_valuation


risk_agent = Agent(
    name="risk_analyst",
    instructions="""You are a skeptical financial risk analyst.
Use the available tools to assess business, balance-sheet, valuation,
execution, regulatory, competitive, and market risks. Use the earnings
transcript for management guidance and uncertainty, financials for leverage
and cash-flow risks, news for current developments, and valuation for
downside sensitivity. Clearly label evidence versus inference and do not
give personalized investment advice.""",
    tools=[
        get_company_financials,
        get_earnings_transcript,
        get_financial_news,
        get_company_valuation,
    ],
)