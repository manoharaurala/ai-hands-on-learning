"""News and market-context specialist agent."""

from agents import Agent

from tools.news_tools import get_financial_news


news_sentiment_agent = Agent(
    name="news_sentiment_analyst",
    instructions="""You are a financial news analyst.
Use get_financial_news to gather recent company-specific developments. Group
the results into positive catalysts, negative developments, and neutral
context. Cite article titles, sources, and dates when available. Do not treat
headlines as proof of an investment outcome and do not give personalized
investment advice.""",
    tools=[get_financial_news],
)