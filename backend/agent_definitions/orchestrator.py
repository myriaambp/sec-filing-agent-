import asyncio
import json
from agents import Agent, Runner, function_tool
from agent_definitions.filing_nlp_agent import filing_nlp_agent
from agent_definitions.market_agent import market_agent
from agent_definitions.analyst_agent import analyst_agent
from typing import AsyncGenerator


# Sector peers lookup for auto-detecting competitors
SECTOR_PEERS = {
    "NVDA": ["AMD", "INTC"],
    "AMD": ["NVDA", "INTC"],
    "INTC": ["NVDA", "AMD"],
    "AAPL": ["MSFT", "GOOG"],
    "MSFT": ["AAPL", "GOOG"],
    "GOOG": ["MSFT", "META"],
    "GOOGL": ["MSFT", "META"],
    "META": ["GOOG", "SNAP"],
    "AMZN": ["MSFT", "GOOG"],
    "TSLA": ["F", "GM"],
    "JPM": ["GS", "MS"],
    "GS": ["JPM", "MS"],
    "MS": ["JPM", "GS"],
    "BAC": ["JPM", "WFC"],
    "WFC": ["BAC", "JPM"],
    "NFLX": ["DIS", "WBD"],
    "DIS": ["NFLX", "CMCSA"],
    "CRM": ["ORCL", "SAP"],
    "V": ["MA", "PYPL"],
    "MA": ["V", "PYPL"],
}

TICKER_PARSER_PROMPT = """You are a ticker extraction assistant.
Given a user question about stocks or companies, extract:
1. The primary ticker symbol(s) the user is asking about
2. Any competitor tickers explicitly mentioned

Return ONLY valid JSON in this exact format:
{"primary_tickers": ["NVDA"], "competitor_tickers": ["AMD"], "form_type": "10-Q"}

Rules:
- Convert company names to ticker symbols (e.g. "Nvidia" -> "NVDA", "Apple" -> "AAPL")
- If the user asks about annual filings or 10-K, set form_type to "10-K"
- Default form_type is "10-Q"
- If user mentions multiple companies to compare, put the first as primary, rest as competitors
- Return ONLY the JSON, no other text
"""

ticker_parser = Agent(
    name="TickerParser",
    instructions=TICKER_PARSER_PROMPT,
    model="gpt-4o-mini",
)


async def run_analysis(user_question: str) -> AsyncGenerator[dict, None]:
    """
    Main orchestration function. Parses question, runs sub-agents in parallel,
    yields progress events and final result.
    """
    # Step 1: Parse question to extract tickers
    yield {"type": "step", "agent": "Orchestrator", "message": "Parsing your question..."}

    parse_result = await Runner.run(ticker_parser, input=user_question)
    try:
        parsed = json.loads(parse_result.final_output)
    except (json.JSONDecodeError, TypeError):
        parsed = {"primary_tickers": [], "competitor_tickers": [], "form_type": "10-Q"}

    primary_tickers = parsed.get("primary_tickers", [])
    competitor_tickers = parsed.get("competitor_tickers", [])
    form_type = parsed.get("form_type", "10-Q")

    if not primary_tickers:
        yield {
            "type": "error",
            "message": "Could not identify any company tickers in your question. Please mention a specific company or ticker symbol.",
        }
        return

    primary = primary_tickers[0]

    # Auto-detect competitors if none specified
    if not competitor_tickers:
        competitor_tickers = SECTOR_PEERS.get(primary.upper(), [])[:2]

    yield {
        "type": "step",
        "agent": "Orchestrator",
        "message": f"Analyzing {primary} (comparing to {', '.join(competitor_tickers) if competitor_tickers else 'no competitors'}) using {form_type} filings",
    }

    # Step 2: Run Filing NLP Agent for primary company
    yield {
        "type": "step",
        "agent": "FilingNLPAgent",
        "message": f"Fetching and analyzing {primary} SEC filings from EDGAR...",
    }

    filing_input = f"Analyze {form_type} filings for ticker {primary}. Fetch and analyze the most recent 6 filings."

    # Run primary filing analysis
    primary_filing_result = await Runner.run(filing_nlp_agent, input=filing_input)
    primary_language = primary_filing_result.final_output

    yield {
        "type": "step",
        "agent": "FilingNLPAgent",
        "message": f"Completed {primary} filing analysis: {primary_language.filings_analyzed} filings analyzed, trend: {primary_language.trend}",
    }

    # Step 3: Run Market Agent and competitor analysis IN PARALLEL
    yield {
        "type": "step",
        "agent": "Orchestrator",
        "message": "Running market signal analysis and competitor analysis in parallel...",
    }

    # Prepare market agent input
    filing_dates = [q.filing_date for q in primary_language.quarterly_scores]
    uncertainty_scores = [q.uncertainty_score for q in primary_language.quarterly_scores]

    market_input = (
        f"Analyze market signal for {primary}. "
        f"Filing dates: {json.dumps(filing_dates)}. "
        f"Uncertainty scores: {json.dumps(uncertainty_scores)}."
    )

    # Build parallel tasks
    tasks = [Runner.run(market_agent, input=market_input)]

    # Add competitor filing analysis tasks
    for comp in competitor_tickers:
        comp_input = f"Analyze {form_type} filings for ticker {comp}. Fetch and analyze the most recent 4 filings."
        tasks.append(Runner.run(filing_nlp_agent, input=comp_input))

    # Run all in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Unpack results
    market_result = results[0]
    if isinstance(market_result, Exception):
        yield {"type": "step", "agent": "MarketSignalAgent", "message": f"Market analysis encountered an issue: {str(market_result)}"}
        market_signal = None
    else:
        market_signal = market_result.final_output
        yield {
            "type": "step",
            "agent": "MarketSignalAgent",
            "message": f"Market signal: {market_signal.signal_strength} — {market_signal.historical_accuracy[:100]}...",
        }

    competitor_signals = []
    for i, comp in enumerate(competitor_tickers):
        comp_result = results[1 + i]
        if isinstance(comp_result, Exception):
            yield {"type": "step", "agent": "FilingNLPAgent", "message": f"Competitor {comp} analysis failed: {str(comp_result)}"}
        else:
            competitor_signals.append(comp_result.final_output)
            yield {
                "type": "step",
                "agent": "FilingNLPAgent",
                "message": f"Competitor {comp}: trend {comp_result.final_output.trend}, {comp_result.final_output.filings_analyzed} filings",
            }

    # Step 4: Run Analyst Agent to synthesize
    yield {
        "type": "step",
        "agent": "AnalystAgent",
        "message": "Synthesizing findings into research memo...",
    }

    # Serialize data for analyst agent
    primary_lang_json = primary_language.model_dump_json()
    market_json = market_signal.model_dump_json() if market_signal else "{}"
    comp_json = json.dumps([c.model_dump() for c in competitor_signals])

    analyst_input = (
        f"Generate an analyst memo for {primary} ({primary_language.company_name}).\n\n"
        f"Primary Language Analysis:\n{primary_lang_json}\n\n"
        f"Market Signal Analysis:\n{market_json}\n\n"
        f"Competitor Language Analysis:\n{comp_json}\n\n"
        f"Original question: {user_question}"
    )

    analyst_result = await Runner.run(analyst_agent, input=analyst_input)
    memo = analyst_result.final_output

    yield {
        "type": "step",
        "agent": "AnalystAgent",
        "message": f"Analysis complete: {memo.recommendation} ({memo.signal}) with {int(memo.confidence * 100)}% confidence",
    }

    # Step 5: Return final result
    yield {"type": "result", "data": memo.model_dump()}
