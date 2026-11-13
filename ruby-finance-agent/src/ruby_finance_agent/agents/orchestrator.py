"""LangGraph coordinator for the typed equity research workflow."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from typing import TypedDict

from agents import Agent, Runner
from agents.exceptions import ModelBehaviorError
from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError

from .config import DEFAULT_AGENT_MODEL, shared_model_settings
from .financial_data_agent import financial_data_agent
from .news_sentiment_agent import news_sentiment_agent
from .report_writer_agent import report_writer_agent
from .risk_agent import risk_agent
from .schemas import (
    EvidenceItem,
    EquityResearchBrief,
    FinancialDataReport,
    NewsSentimentReport,
    ReportSynthesis,
    RiskVerdict,
    RiskReport,
    ValuationReport,
    ValuationVerdict,
)
from .valuation_agent import valuation_agent


class ResearchState(TypedDict, total=False):
    """Typed graph handoffs; each node writes its own output and error key."""

    request: str
    financial_analysis: FinancialDataReport | None
    financial_error: str
    news_analysis: NewsSentimentReport | None
    news_error: str
    risk_analysis: RiskReport | None
    risk_error: str
    first_stage_joined: bool
    valuation_analysis: ValuationReport | None
    valuation_error: str
    final_report: EquityResearchBrief | None
    report_error: str
    fallback_used: bool


orchestrator = Agent(
    name="finance_research_orchestrator",
    instructions=(
        "Coordinate the staged research graph. Do not perform independent "
        "analysis or call tools."
    ),
    tools=[],
    model=DEFAULT_AGENT_MODEL,
    model_settings=shared_model_settings(),
)


async def _run_specialist(agent: Agent, request: str, output_type: type):
    result = await Runner.run(agent, request)
    output = result.final_output
    if not isinstance(output, output_type):
        raise TypeError("specialist returned an unexpected output schema")
    return output


async def _run_or_record(
    agent_name: str, agent: Agent, prompt: str, output_type: type
):
    try:
        return await _run_specialist(agent, prompt, output_type), ""
    except ValidationError as exc:
        errors = exc.errors(include_input=False, include_url=False)
        fields = sorted(
            {
                ".".join(str(part) for part in error["loc"]) or "<root>"
                for error in errors
            }
        )
        issue_types = sorted({error["type"] for error in errors})
        return None, (
            f"{agent_name} output failed schema validation; fields: "
            f"{', '.join(fields[:8]) or '<unknown>'}; "
            f"issue types: {', '.join(issue_types[:5]) or 'unknown'}"
        )
    except ModelBehaviorError:
        # SDK messages may embed the raw model response; report only a safe
        # category and let the deterministic fallback preserve specialist data.
        return None, (
            f"{agent_name} returned an unsupported or malformed model response "
            "(ModelBehaviorError)"
        )
    except Exception as exc:
        # Exception text may contain request details; retain only its type.
        return None, f"{agent_name} failed ({type(exc).__name__})"


def _serialize(value: object | None, error: str) -> str:
    if value is None:
        return f"Unavailable: {error or 'no validated output was returned.'}"
    return value.model_dump_json(indent=2)


def _source_evidence(state: ResearchState) -> list[EvidenceItem]:
    """Collect evidence and source URLs from the typed specialist reports."""
    evidence = []
    seen = set()
    financial = state.get("financial_analysis")
    valuation = state.get("valuation_analysis")
    risk = state.get("risk_analysis")
    if financial is not None:
        evidence.extend(financial.evidence)
    if valuation is not None:
        evidence.extend(valuation.evidence)
    if risk is not None:
        for item in risk.risks:
            evidence.extend(item.evidence)
    unique = []
    for item in evidence:
        key = item.model_dump_json()
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def _risk_verdict(report: RiskReport | None) -> tuple[RiskVerdict, str]:
    """Derive the overall risk level from the displayed risk register."""
    if report is None or not report.risks:
        return "UNKNOWN", "No rated risk items were supplied."
    severities = {item.severity for item in report.risks}
    likelihoods = {item.likelihood for item in report.risks}
    if "HIGH" in severities or "HIGH" in likelihoods:
        return "HIGH", "At least one listed risk has a HIGH rating."
    if "MEDIUM" in severities:
        return "ELEVATED", "At least one listed risk has MEDIUM severity."
    if "MEDIUM" in likelihoods:
        return "MODERATE", "At least one listed risk has MEDIUM likelihood."
    rated = severities | likelihoods
    if "LOW" in rated:
        return "LOW", "Listed risks are LOW or UNKNOWN; none is MEDIUM or HIGH."
    return "UNKNOWN", "The supplied risk ratings are all UNKNOWN."


def _has_valuation_support(report: ValuationReport | None) -> bool:
    """Check whether structured comparisons support a valuation verdict."""
    if report is None:
        return False
    unavailable = {"N/A", "NA", "NONE", "UNAVAILABLE"}
    has_peer_values = any(
        multiple.data_status == "MEANINGFUL"
        and multiple.value
        and multiple.value.strip().upper() not in unavailable
        for peer in report.peer_comparisons
        for multiple in peer.multiples
    )
    dcf = report.dcf
    dcf_values = (
        (
            dcf.per_share_value,
            dcf.current_price,
            dcf.upside_or_downside,
        )
        if dcf
        else ()
    )
    has_dcf_comparison = bool(
        dcf_values
        and all(
            value and value.strip().upper() not in unavailable
            for value in dcf_values
        )
    )
    return has_peer_values or has_dcf_comparison


def _valuation_verdict(
    report: ValuationReport | None,
) -> ValuationVerdict | None:
    """Avoid a directional verdict without structured valuation support."""
    if report is None:
        return None
    return report.verdict if _has_valuation_support(report) else "INCONCLUSIVE"


def _unique_text(items: list[str]) -> list[str]:
    """Keep non-empty caveat/monitoring text in first-seen order."""
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


async def _financial_data_node(state: ResearchState) -> dict[str, object]:
    prompt = f"""Analyze the company in the request using the financial
statement tools.
Populate the FinancialDataReport schema. Use only returned facts; include
reported periods, units, source evidence, a fixed verdict, and data caveats.

Company research request:\n{state['request']}"""
    output, error = await _run_or_record(
        "FinancialDataAgent", financial_data_agent, prompt, FinancialDataReport
    )
    return {"financial_analysis": output, "financial_error": error}


async def _news_sentiment_node(state: ResearchState) -> dict[str, object]:
    prompt = f"""Analyze recent company-specific news using the news tool.
Populate NewsSentimentReport. Preserve returned headlines, publishers,
publication times, and URLs. Use a fixed sentiment label and state coverage
caveats.

Company research request:\n{state['request']}"""
    output, error = await _run_or_record(
        "NewsSentimentAgent", news_sentiment_agent, prompt, NewsSentimentReport
    )
    return {"news_analysis": output, "news_error": error}


async def _risk_node(state: ResearchState) -> dict[str, object]:
    prompt = f"""Assess company risks with available tools. Populate RiskReport.
Include evidence, periods/as-of dates, fixed severity/likelihood labels, and
assumption-labelled BASE and DOWNSIDE scenarios. Do not invent figures.

Company research request:\n{state['request']}"""
    output, error = await _run_or_record(
        "RiskAgent", risk_agent, prompt, RiskReport
    )
    return {"risk_analysis": output, "risk_error": error}


def _join_first_stage(_: ResearchState) -> dict[str, bool]:
    return {"first_stage_joined": True}


async def _valuation_node(state: ResearchState) -> dict[str, object]:
    financial_json = _serialize(
        state.get("financial_analysis"), state.get("financial_error", "")
    )
    prompt = f"""Analyze valuation and populate ValuationReport. State its DCF
assumptions, periods, currency, peer set, missing data, and caveats. Do not
invent data. The financial report below is validated JSON context.

Company research request:\n{state['request']}

FinancialDataReport JSON:\n{financial_json}"""
    output, error = await _run_or_record(
        "ValuationAgent", valuation_agent, prompt, ValuationReport
    )
    return {"valuation_analysis": output, "valuation_error": error}


def _build_research_brief(
    state: ResearchState,
    synthesis: ReportSynthesis | None,
) -> EquityResearchBrief:
    """Assemble the final brief from validated specialist reports."""
    financial = state.get("financial_analysis")
    news = state.get("news_analysis")
    risk = state.get("risk_analysis")
    valuation = state.get("valuation_analysis")
    risk_verdict, risk_rationale = _risk_verdict(risk)
    valuation_verdict = _valuation_verdict(valuation)
    sentiment_verdict = (
        news.sentiment
        if news is not None and news.articles
        else "INSUFFICIENT_DATA"
    )
    financial_verdict = financial.verdict if financial else None
    labels = (
        f"financial health {financial_verdict or 'UNAVAILABLE'}, "
        f"news sample {sentiment_verdict}, "
        f"overall risk {risk_verdict if risk else 'UNAVAILABLE'}, "
        f"valuation {valuation_verdict or 'UNAVAILABLE'}"
    )
    executive_summary = (
        synthesis.executive_summary.strip()
        if synthesis and synthesis.executive_summary.strip()
        else f"Structured specialist classifications: {labels}."
    )
    conclusion = (
        synthesis.conclusion.strip()
        if synthesis and synthesis.conclusion.strip()
        else (
            "This educational brief summarizes the supplied specialist "
            "data and assumptions only. Missing inputs and source limitations "
            "are listed below; these results do not establish future "
            "performance or a personal investment decision."
        )
    )

    if not _has_valuation_support(valuation):
        limitation = (
            "Structured valuation inputs do not support a directional "
            "valuation conclusion."
        )
        executive_summary = f"{executive_summary} {limitation}"
        conclusion = f"{conclusion} {limitation}"

    caveats = []
    if financial is not None:
        caveats.extend(financial.missing_data_and_caveats)
    if news is not None:
        caveats.extend(news.caveats)
        caveats.extend(
            f"Article URL unavailable: {article.headline}"
            for article in news.articles
            if not article.url
        )
    if risk is not None:
        caveats.extend(risk.missing_data_and_caveats)
    if valuation is not None:
        caveats.extend(valuation.caveats)
        if not _has_valuation_support(valuation):
            caveats.append(
                "No usable DCF comparison or meaningful peer multiples were "
                "supplied; relative valuation cannot be concluded."
            )
    else:
        caveats.append("Valuation data is unavailable.")
    if news is None or not news.articles:
        caveats.append("No sourced company news articles were supplied.")
    if synthesis is None:
        caveats.append(
            "Report synthesis failed; this brief was assembled "
            "deterministically from completed specialist data."
        )

    symbol = next(
        (
            report.symbol
            for report in (financial, news, risk, valuation)
            if report is not None
        ),
        None,
    )
    if symbol is None:
        match = re.search(
            r"\bticker\s*:\s*([A-Z0-9.^=\-]{1,20})",
            state.get("request", ""),
            flags=re.IGNORECASE,
        )
        symbol = match.group(1).upper() if match else "UNKNOWN"

    monitoring = (
        [item.monitoring_signal for item in risk.risks]
        if risk is not None
        else []
    )
    return EquityResearchBrief.model_validate(
        {
            "symbol": symbol,
            "executive_summary": executive_summary,
            "financial_verdict": financial_verdict,
            "sentiment_verdict": sentiment_verdict,
            "risk_verdict": risk_verdict if risk is not None else None,
            "valuation_verdict": valuation_verdict,
            "financial_report": financial,
            "financial_unit_caveat": (
                "Yahoo Finance annual statement responses do not label "
                "currency or units; none has been inferred from the ticker "
                "or exchange."
            ),
            "news_report": news,
            "valuation_report": valuation,
            "dcf_scenario": valuation.dcf if valuation is not None else None,
            "evidence": _source_evidence(state),
            "risk_register": risk.risks if risk is not None else [],
            "risk_verdict_rationale": (
                risk_rationale if risk is not None else None
            ),
            "stress_scenarios": (
                risk.stress_scenarios if risk is not None else []
            ),
            "key_evidence_and_disagreements": (
                synthesis.key_points if synthesis is not None else []
            ),
            "missing_data_and_uncertainties": _unique_text(caveats),
            "monitoring_items": _unique_text(monitoring),
            "conclusion": conclusion,
        }
    )


async def _report_writer_node(state: ResearchState) -> dict[str, object]:
    # Serialize validated Pydantic values explicitly for stable handoffs.
    specialist_outputs = {
        "financial_data": _serialize(
            state.get("financial_analysis"), state.get("financial_error", "")
        ),
        "news_sentiment": _serialize(
            state.get("news_analysis"), state.get("news_error", "")
        ),
        "risk": _serialize(
            state.get("risk_analysis"), state.get("risk_error", "")
        ),
        "valuation": _serialize(
            state.get("valuation_analysis"), state.get("valuation_error", "")
        ),
    }
    prompt = f"""Synthesize the validated specialist JSON into a concise
ReportSynthesis with only executive_summary, conclusion, and key_points. Use
only supplied evidence; preserve uncertainty and disagreements. Do not repeat
the disclaimer in conclusion. Treat Unavailable markers as workflow errors,
not company evidence.

Company research request:\n{state['request']}

Specialist reports:\n{json.dumps(specialist_outputs, indent=2)}"""
    output, error = await _run_or_record(
        "ReportWriterAgent", report_writer_agent, prompt, ReportSynthesis
    )
    report = _build_research_brief(state, output)
    return {
        "final_report": report,
        "report_error": error,
        "fallback_used": output is None,
    }


def _build_research_graph():
    graph = StateGraph(ResearchState)
    graph.add_node("financial_data", _financial_data_node)
    graph.add_node("news_sentiment", _news_sentiment_node)
    graph.add_node("risk", _risk_node)
    graph.add_node("join", _join_first_stage)
    graph.add_node("valuation", _valuation_node)
    graph.add_node("report_writer", _report_writer_node)
    graph.add_edge(START, "financial_data")
    graph.add_edge(START, "news_sentiment")
    graph.add_edge(START, "risk")
    graph.add_edge(["financial_data", "news_sentiment", "risk"], "join")
    graph.add_edge("join", "valuation")
    graph.add_edge("valuation", "report_writer")
    graph.add_edge("report_writer", END)
    return graph.compile()


_research_graph = _build_research_graph()


async def run_research_workflow(request: str) -> str:
    """Run the typed parallel workflow and render its validated brief."""
    if not isinstance(request, str):
        raise TypeError("Research request must be text.")
    request = request.strip()
    if not request:
        raise ValueError("Research request cannot be empty.")
    state = await _research_graph.ainvoke({"request": request})
    report = state.get("final_report")
    if not isinstance(report, EquityResearchBrief):
        errors = [
            state[key]
            for key in (
                "financial_error",
                "news_error",
                "risk_error",
                "valuation_error",
                "report_error",
            )
            if state.get(key)
        ]
        status = (
            "; ".join(errors)
            if errors
            else "ReportWriterAgent returned no validated brief"
        )
        return f"[Research workflow incomplete: {status}]"
    return report.to_markdown()


# Progress routing handles graph nodes, errors, fallback, and final output.
# pylint: disable=too-many-branches
async def stream_research_workflow(
    request: str,
) -> AsyncIterator[tuple[str, str]]:
    """Yield progress and the final Markdown brief from the same graph."""
    if not isinstance(request, str):
        raise TypeError("Research request must be text.")
    request = request.strip()
    if not request:
        raise ValueError("Research request cannot be empty.")

    labels = {
        "financial_data": "Financial data",
        "news_sentiment": "News and sentiment",
        "risk": "Risk assessment",
        "valuation": "Valuation",
        "report_writer": "Report synthesis",
    }
    error_fields = {
        "financial_data": "financial_error",
        "news_sentiment": "news_error",
        "risk": "risk_error",
        "valuation": "valuation_error",
        "report_writer": "report_error",
    }
    final_report = None
    fallback_used = False
    errors = []
    try:
        async for update in _research_graph.astream(
            {"request": request}, stream_mode="updates"
        ):
            for node, node_state in update.items():
                if node == "join":
                    yield (
                        "Parallel research complete; valuation is starting.",
                        "",
                    )
                    continue
                if node not in labels:
                    continue
                error = node_state.get(error_fields[node])
                if error:
                    message = f"{labels[node]} reported an error: {error}."
                    errors.append(message)
                    candidate = node_state.get("final_report")
                    if node == "report_writer" and isinstance(
                        candidate, EquityResearchBrief
                    ):
                        final_report = candidate
                        fallback_used = bool(
                            node_state.get("fallback_used", True)
                        )
                        yield (
                            "⚠ "
                            f"{message} Using a deterministic brief from "
                            "validated specialist reports.",
                            "",
                        )
                    else:
                        yield f"⚠ {message}", ""
                    continue
                if node == "report_writer":
                    report = node_state.get("final_report")
                    if isinstance(report, EquityResearchBrief):
                        final_report = report
                        fallback_used = bool(
                            node_state.get("fallback_used", False)
                        )
                    else:
                        yield (
                            "Report synthesis returned no validated report.",
                            "",
                        )
                    continue
                yield f"✓ {labels[node]} complete.", ""
    except Exception as exc:
        message = f"Workflow stopped ({type(exc).__name__})."
        errors.append(message)
        yield message, ""
        return

    if final_report is not None:
        status = (
            "Research complete with deterministic fallback."
            if fallback_used
            else "Research complete."
        )
        yield status, final_report.to_markdown()
    else:
        detail = " ".join(errors) or "No validated report was returned."
        yield f"Research incomplete: {detail}", ""
