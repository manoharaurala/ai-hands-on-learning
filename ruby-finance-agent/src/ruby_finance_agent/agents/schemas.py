"""Validated specialist outputs and deliberate Markdown serialization."""

from collections.abc import Callable
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field


class ResearchModel(BaseModel):
    """Base model that rejects fields outside the declared schema."""

    model_config = ConfigDict(extra="forbid")


class EvidenceItem(ResearchModel):
    """A claim tied to its source and reporting period."""

    claim: str
    source: str
    period_or_published_at: str = Field(
        description="Reporting period or publication/as-of time"
    )
    url: str | None = None
    currency_or_unit: str | None = None
    evidence_type: Literal["REPORTED", "ANALYSIS", "ASSUMPTION"]


FinancialVerdict = Literal["STRONG", "SOLID", "MIXED", "WEAK"]
SentimentVerdict = Literal[
    "BULLISH", "BEARISH", "MIXED", "NEUTRAL", "INSUFFICIENT_DATA"
]
RiskLevel = Literal["HIGH", "MEDIUM", "LOW", "UNKNOWN"]
RiskVerdict = Literal["LOW", "MODERATE", "ELEVATED", "HIGH", "UNKNOWN"]
ValuationVerdict = Literal[
    "SIGNIFICANTLY_UNDERVALUED",
    "SLIGHTLY_UNDERVALUED",
    "FAIRLY_VALUED",
    "SLIGHTLY_OVERVALUED",
    "SIGNIFICANTLY_OVERVALUED",
    "INCONCLUSIVE",
]


class FinancialTrend(ResearchModel):
    """A reported metric across annual statement periods."""

    metric: str
    period_values: list[str] = Field(default_factory=list)
    analysis: str


class FinancialDataReport(ResearchModel):
    """Validated company financial-health assessment."""

    symbol: str
    company_name: str | None = None
    coverage_and_periods: str
    verdict: FinancialVerdict
    rationale: str
    trends: list[FinancialTrend] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    missing_data_and_caveats: list[str] = Field(default_factory=list)


class NewsArticle(ResearchModel):
    """A retrieved article with publisher and publication metadata."""

    headline: str
    publisher: str
    published_at: str
    url: str | None = None
    summary: str
    tone: Literal["POSITIVE", "NEGATIVE", "MIXED", "NEUTRAL", "UNCLEAR"]


class NewsSentimentReport(ResearchModel):
    """Validated summary of the retrieved company-news sample."""

    symbol: str
    provider_and_coverage: str
    date_range: str | None = None
    sentiment: SentimentVerdict
    rationale: str
    articles: list[NewsArticle] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class RiskItem(ResearchModel):
    """A company risk with evidence, ratings, impact, and a signal."""

    risk: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    severity: RiskLevel
    likelihood: RiskLevel
    possible_impact: str
    monitoring_signal: str


class StressScenario(ResearchModel):
    """An assumption-labelled base or downside scenario."""

    scenario: Literal["BASE", "DOWNSIDE"]
    assumptions: list[str] = Field(default_factory=list)
    possible_effects: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class RiskReport(ResearchModel):
    """Validated evidence-based company risk assessment."""

    symbol: str
    coverage_and_periods: str
    verdict: RiskVerdict
    verdict_rationale: str
    risks: list[RiskItem] = Field(default_factory=list)
    stress_scenarios: list[StressScenario] = Field(default_factory=list)
    missing_data_and_caveats: list[str] = Field(default_factory=list)


class DCFScenario(ResearchModel):
    """Assumptions and output from an illustrative DCF scenario."""

    assumptions: list[str] = Field(default_factory=list)
    statement_period_or_as_of: str | None = None
    currency: str | None = None
    free_cash_flow_basis: str
    per_share_value: str | None = None
    current_price: str | None = None
    upside_or_downside: str | None = None
    caveats: list[str] = Field(default_factory=list)


class PeerComparison(ResearchModel):
    """Reported valuation multiples for one named company."""

    ticker: str
    company_name: str | None = None
    period_or_as_of: str | None = None
    currency: str | None = None
    multiples: list["MultipleValue"] = Field(default_factory=list)
    interpretation: str


class MultipleValue(ResearchModel):
    """A peer multiple with an explicit meaningfulness status."""

    metric: str
    value: str | None = None
    data_status: Literal["MEANINGFUL", "NOT_MEANINGFUL", "MISSING"]
    note: str | None = None


class ValuationReport(ResearchModel):
    """Validated valuation summary with assumptions and caveats."""

    symbol: str
    verdict: ValuationVerdict
    summary: str
    current_quote_and_as_of: str | None = None
    dcf: DCFScenario | None = None
    peer_set: list[str] = Field(default_factory=list)
    peer_comparisons: list[PeerComparison] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class ReportSynthesis(ResearchModel):
    """Small narrative output from the synthesis-only writer agent."""

    executive_summary: str
    conclusion: str
    key_points: list[str] = Field(default_factory=list)


DISCLAIMER = (
    "This report is for educational purposes only and is not "
    "financial advice."
)


class EquityResearchBrief(ResearchModel):
    """Final synthesis of specialist reports with citations."""

    symbol: str
    executive_summary: str
    financial_verdict: FinancialVerdict | None = None
    sentiment_verdict: SentimentVerdict | None = None
    risk_verdict: RiskVerdict | None = None
    valuation_verdict: ValuationVerdict | None = None
    financial_report: FinancialDataReport | None = None
    financial_unit_caveat: str = (
        "Yahoo Finance annual statements do not state currency or units; "
        "none has been inferred from the ticker or exchange."
    )
    news_report: NewsSentimentReport | None = None
    valuation_report: ValuationReport | None = None
    dcf_scenario: DCFScenario | None = None
    evidence: list[EvidenceItem]
    risk_register: list[RiskItem] = Field(default_factory=list)
    risk_verdict_rationale: str | None = None
    stress_scenarios: list[StressScenario] = Field(default_factory=list)
    key_evidence_and_disagreements: list[str] = Field(default_factory=list)
    missing_data_and_uncertainties: list[str] = Field(default_factory=list)
    monitoring_items: list[str] = Field(default_factory=list)
    conclusion: str
    disclaimer: Literal[
        "This report is for educational purposes only and is not "
        "financial advice."
    ] = DISCLAIMER

    def to_markdown(self) -> str:
        """Render a stable, human-readable brief from validated fields."""

        def bullets(items: list[str]) -> str:
            return (
                "\n".join(f"- {item}" for item in items)
                if items
                else "- None reported."
            )

        def citation(label: str, url: str | None) -> str:
            parsed = urlparse(url or "")
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                safe_label = (
                    label.replace("\\", "\\\\")
                    .replace("[", "\\[")
                    .replace("]", "\\]")
                )
                if safe_label.strip().lower() in {
                    "source",
                    "url",
                    "link",
                    "unknown",
                }:
                    safe_label = "Open evidence link"
                return f"[{safe_label}](<{url}>)"
            return f"{label} (URL unavailable)"

        evidence = (
            "\n".join(
                f"- {item.claim} — {item.source}; "
                f"{item.period_or_published_at}; "
                f"{citation(item.source, item.url)}"
                for item in self.evidence
            )
            or "- No linked evidence was supplied."
        )
        risks = (
            "\n".join(
                f"- **{risk.risk}** — severity {risk.severity}; "
                f"likelihood {risk.likelihood}. "
                f"Impact: {risk.possible_impact} "
                f"Monitoring: {risk.monitoring_signal} "
                + (
                    "Evidence: "
                    + "; ".join(
                        f"{item.claim} ({citation(item.source, item.url)})"
                        for item in risk.evidence
                    )
                    if risk.evidence
                    else "Evidence not supplied."
                )
                for risk in self.risk_register
            )
            or "- No risk items reported."
        )
        scenarios = (
            "\n".join(
                f"- **{scenario.scenario.title()} case.** "
                "Assumptions: "
                f"{', '.join(scenario.assumptions) or 'Not specified.'} "
                f"Possible effects: "
                f"{', '.join(scenario.possible_effects) or 'Not specified.'}"
                for scenario in self.stress_scenarios
            )
            or "- No scenarios reported."
        )
        risk_rationale = (
            self.risk_verdict_rationale or "Overall risk rating unavailable."
        )
        sections = [
            f"# {self.symbol} Equity Research Brief",
            f"## Executive summary\n{self.executive_summary}",
            "## Specialist verdicts\n"
            "- Financial health: **"
            f"{self.financial_verdict or 'UNAVAILABLE'}**\n"
            "- News sentiment: **"
            f"{self.sentiment_verdict or 'UNAVAILABLE'}**\n"
            f"- Overall risk: **{self.risk_verdict or 'UNAVAILABLE'}**\n"
            f"- Valuation: **{self.valuation_verdict or 'UNAVAILABLE'}**",
            f"## Financial health and performance\n"
            f"{self._render_financial()}\n\n"
            f"**Statement currency/unit caveat:** "
            f"{self.financial_unit_caveat}",
            f"## News and sentiment\n{self._render_news(citation)}",
            f"## Valuation ({self.valuation_verdict or 'UNAVAILABLE'})\n"
            f"{self._render_valuation()}",
            f"## Risk register ({self.risk_verdict or 'UNKNOWN'})\n"
            f"{risk_rationale}"
            f"\n\n{risks}\n\n### Stress scenarios\n{scenarios}",
            "## Key evidence and disagreements\n"
            f"{bullets(self.key_evidence_and_disagreements)}",
            f"## Linked evidence\n{evidence}",
            "## Missing data and uncertainties\n"
            f"{bullets(self.missing_data_and_uncertainties)}",
            f"## Monitoring items\n{bullets(self.monitoring_items)}",
            f"## Conclusion\n{self.conclusion}",
        ]
        report = "\n\n".join(sections).replace(self.disclaimer, "").rstrip()
        return f"{report}\n\n{self.disclaimer}"

    def _render_financial(self) -> str:
        """Render financial findings from the validated specialist report."""
        financial = self.financial_report
        if financial is None:
            return "Financial data is unavailable."
        lines = [
            f"- Coverage: {financial.coverage_and_periods}",
            f"- Verdict: {financial.verdict}",
            f"- Rationale: {financial.rationale}",
        ]
        for trend in financial.trends:
            values = "; ".join(trend.period_values) or "Values unavailable."
            lines.append(
                f"- {trend.metric}: {values}. Analysis: {trend.analysis}"
            )
        if financial.missing_data_and_caveats:
            lines.append(
                "- Caveats: " + "; ".join(financial.missing_data_and_caveats)
            )
        return "\n".join(lines)

    def _render_news(self, citation: Callable[[str, str | None], str]) -> str:
        """Render only structured news fields and exact source URLs."""
        news = self.news_report
        if news is None:
            return (
                "News results are unavailable; "
                "no sourced articles were supplied."
            )
        sentiment = news.sentiment if news.articles else "INSUFFICIENT_DATA"
        articles = (
            "\n".join(
                f"- {citation(article.headline, article.url)} — "
                f"{article.publisher}; {article.published_at}; "
                f"{article.tone}. {article.summary}"
                for article in news.articles
            )
            or "- No sourced company news articles were returned."
        )
        lines = [
            f"Sample verdict: {sentiment}. This label summarizes the "
            "retrieved news sample; it is not a measured market sentiment "
            "score or a share-price forecast.",
            f"Coverage: {news.provider_and_coverage}",
        ]
        if news.date_range:
            lines.append(f"Date range: {news.date_range}")
        lines.append(articles)
        if news.risk_flags:
            lines.append("Risk flags: " + "; ".join(news.risk_flags))
        if news.caveats:
            lines.append("Caveats: " + "; ".join(news.caveats))
        return "\n\n".join(lines)

    def _render_valuation(self) -> str:
        """Render only structured valuation evidence and disclosed gaps."""
        valuation = self.valuation_report
        if valuation is None:
            return "Valuation inputs are unavailable."
        lines = []
        if valuation.current_quote_and_as_of:
            lines.append(
                "- Provider quote: " + valuation.current_quote_and_as_of
            )
        lines.append(self._render_dcf())
        comparisons = valuation.peer_comparisons
        if not comparisons:
            lines.append(
                "- No explicit peer comparisons were supplied; relative "
                "valuation multiples cannot be assessed."
            )
        else:
            lines.append("### Peer comparisons")
            if valuation.peer_set:
                lines.append("- Peer set: " + ", ".join(valuation.peer_set))
            for peer in comparisons:
                label = peer.ticker
                if peer.company_name:
                    label += f" ({peer.company_name})"
                if peer.period_or_as_of:
                    label += f"; as of/period {peer.period_or_as_of}"
                if peer.currency:
                    label += f"; currency {peer.currency}"
                lines.append(f"- **{label}**")
                if not peer.multiples:
                    lines.append("  - Multiples: unavailable.")
                for multiple in peer.multiples:
                    value = multiple.value or "value unavailable"
                    note = f"; {multiple.note}" if multiple.note else ""
                    lines.append(
                        f"  - {multiple.metric}: {value} "
                        f"({multiple.data_status}{note})"
                    )
        if valuation.caveats:
            lines.append("- Caveats: " + "; ".join(valuation.caveats))
        return "\n".join(lines)

    def _render_dcf(self) -> str:
        """Render the scenario values required in the sample brief."""
        scenario = self.dcf_scenario
        if scenario is None:
            return "### Illustrative DCF scenario\n- Not available."
        lines = ["### Illustrative DCF scenario"]
        if scenario.per_share_value:
            lines.append(
                f"- Scenario value per share: {scenario.per_share_value}"
            )
        if scenario.current_price:
            lines.append(f"- Current price: {scenario.current_price}")
        if scenario.upside_or_downside:
            lines.append(
                f"- Implied upside/downside: {scenario.upside_or_downside}"
            )
        if scenario.statement_period_or_as_of:
            lines.append(
                "- Statement period/as of: "
                f"{scenario.statement_period_or_as_of}"
            )
        if scenario.currency:
            lines.append(f"- Currency: {scenario.currency}")
        lines.append(f"- Cash-flow basis: {scenario.free_cash_flow_basis}")
        lines.append(
            "- Assumptions: "
            + (", ".join(scenario.assumptions) or "Not specified.")
        )
        if scenario.caveats:
            lines.append("- Caveats: " + "; ".join(scenario.caveats))
        return "\n".join(lines)
