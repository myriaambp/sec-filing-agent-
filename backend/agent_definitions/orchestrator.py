import asyncio
import json
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
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
    model="gemini-2.0-flash",
    name="ticker_parser",
    description="Extracts stock ticker symbols from user questions",
    instruction=TICKER_PARSER_PROMPT,
)


async def _run_agent(agent: Agent, message: str, app_name: str = "filinglens") -> str:
    """Run a single agent and return its final text response."""
    runner = InMemoryRunner(agent=agent, app_name=app_name)
    user_id = "user"

    session = await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id,
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=types.Content(
            role="user",
            parts=[types.Part(text=message)],
        ),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text += part.text

    return final_text


async def run_analysis(user_question: str) -> AsyncGenerator[dict, None]:
    """
    Main orchestration function. Parses question, runs sub-agents in parallel,
    yields progress events and final result.
    """
    # Step 1: Parse question to extract tickers
    yield {"type": "step", "agent": "Orchestrator", "message": "Parsing your question..."}

    parse_output = await _run_agent(ticker_parser, user_question)
    try:
        # Strip markdown code fences if present
        clean = parse_output.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        parsed = json.loads(clean)
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
    primary_lang_raw = await _run_agent(filing_nlp_agent, filing_input)

    # Parse the agent's JSON response
    try:
        clean = primary_lang_raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        primary_language = json.loads(clean)
    except (json.JSONDecodeError, TypeError):
        primary_language = {"error": "Failed to parse filing analysis", "raw": primary_lang_raw[:200]}

    filings_count = primary_language.get("filings_analyzed", 0)
    trend = primary_language.get("trend", "unknown")

    # Check if we got an error or no filings
    if primary_language.get("error") or filings_count == 0:
        error_msg = primary_language.get("error", f"No SEC filings found for {primary}. It may not be a valid public company ticker.")
        yield {"type": "error", "message": error_msg}
        return

    # Fetch filing metadata directly for source links (don't rely on LLM passing these through)
    from tools.fetch_filings import fetch_recent_filings, get_cik_for_ticker
    primary_filings_meta = fetch_recent_filings(primary, form_type, 6)
    primary_cik = get_cik_for_ticker(primary)
    primary_cik_clean = primary_cik.lstrip("0") if primary_cik else ""
    primary_filing_sources = []
    edgar_company_page = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={primary}&type={form_type}&dateb=&owner=include&count=40"
    for f in primary_filings_meta:
        acc_no_dashes = f["accession_number"].replace("-", "")
        primary_filing_sources.append({
            "period": f["period"],
            "filing_date": f["filing_date"],
            "form_type": form_type,
            "url": f"https://www.sec.gov/Archives/edgar/data/{primary_cik_clean}/{acc_no_dashes}/{f['primary_doc']}",
            "accession_number": f["accession_number"],
        })

    yield {
        "type": "step",
        "agent": "FilingNLPAgent",
        "message": f"Completed {primary} filing analysis: {filings_count} filings analyzed, trend: {trend}",
    }

    # Step 3: Run Market Agent and competitor analysis IN PARALLEL
    yield {
        "type": "step",
        "agent": "Orchestrator",
        "message": "Running market signal analysis and competitor analysis in parallel...",
    }

    # Prepare market agent input
    quarterly_scores = primary_language.get("quarterly_scores", [])
    filing_dates = [q["filing_date"] for q in quarterly_scores]
    uncertainty_scores = [q["uncertainty_score"] for q in quarterly_scores]

    market_input = (
        f"Analyze market signal for {primary}. "
        f"Filing dates: {json.dumps(filing_dates)}. "
        f"Uncertainty scores: {json.dumps(uncertainty_scores)}."
    )

    # Build parallel tasks
    tasks = [_run_agent(market_agent, market_input)]

    for comp in competitor_tickers:
        comp_input = f"Analyze {form_type} filings for ticker {comp}. Fetch and analyze the most recent 4 filings."
        tasks.append(_run_agent(filing_nlp_agent, comp_input))

    # Run all in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Unpack market result
    market_signal = {}
    market_raw = results[0]
    if isinstance(market_raw, Exception):
        yield {"type": "step", "agent": "MarketSignalAgent", "message": f"Market analysis issue: {str(market_raw)}"}
    else:
        try:
            clean = market_raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                if clean.endswith("```"):
                    clean = clean[:-3]
                clean = clean.strip()
            market_signal = json.loads(clean)
            yield {
                "type": "step",
                "agent": "MarketSignalAgent",
                "message": f"Market signal: {market_signal.get('signal_strength', 'unknown')} — {market_signal.get('historical_accuracy', '')[:100]}",
            }
        except (json.JSONDecodeError, TypeError):
            yield {"type": "step", "agent": "MarketSignalAgent", "message": "Market analysis completed (parsing issue)"}

    # Unpack competitor results
    competitor_signals = []
    for i, comp in enumerate(competitor_tickers):
        comp_raw = results[1 + i]
        if isinstance(comp_raw, Exception):
            yield {"type": "step", "agent": "FilingNLPAgent", "message": f"Competitor {comp} analysis failed: {str(comp_raw)}"}
        else:
            try:
                clean = comp_raw.strip()
                if clean.startswith("```"):
                    clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
                    if clean.endswith("```"):
                        clean = clean[:-3]
                    clean = clean.strip()
                comp_data = json.loads(clean)
                competitor_signals.append(comp_data)
                yield {
                    "type": "step",
                    "agent": "FilingNLPAgent",
                    "message": f"Competitor {comp}: trend {comp_data.get('trend', 'unknown')}, {comp_data.get('filings_analyzed', 0)} filings",
                }
            except (json.JSONDecodeError, TypeError):
                yield {"type": "step", "agent": "FilingNLPAgent", "message": f"Competitor {comp} completed (parsing issue)"}

    # Step 4: Run Analyst Agent to synthesize
    yield {
        "type": "step",
        "agent": "AnalystAgent",
        "message": "Synthesizing findings into research memo...",
    }

    analyst_input = (
        f"Generate an analyst memo for {primary} ({primary_language.get('company_name', primary)}).\n\n"
        f"Primary Language Analysis:\n{json.dumps(primary_language, indent=2)}\n\n"
        f"Market Signal Analysis:\n{json.dumps(market_signal, indent=2)}\n\n"
        f"Competitor Language Analysis:\n{json.dumps(competitor_signals, indent=2)}\n\n"
        f"Original question: {user_question}"
    )

    analyst_raw = await _run_agent(analyst_agent, analyst_input)

    try:
        clean = analyst_raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
        memo = json.loads(clean)
    except (json.JSONDecodeError, TypeError):
        memo = {
            "company": primary,
            "company_name": primary_language.get("company_name", primary),
            "competitors_analyzed": competitor_tickers,
            "recommendation": "HOLD",
            "signal": "CAUTIONARY",
            "confidence": 0.5,
            "language_trend": trend,
            "uncertainty_score_change": f"{primary_language.get('trend_magnitude', 0):.1f}%",
            "key_evidence": ["Analysis completed but structured output parsing failed"],
            "historical_context": market_signal.get("historical_accuracy", ""),
            "competitor_comparison": "",
            "full_memo": analyst_raw,
            "chart_base64": "",
        }

    # Generate chart directly in orchestrator (LLM can't pass through large base64)
    from utils.chart_generator import generate_sentiment_vs_price_chart
    from tools.fetch_prices import fetch_price_history

    price_df = fetch_price_history(primary, period="2y")
    price_data = []
    if not price_df.empty:
        sampled = price_df.iloc[::5] if len(price_df) > 50 else price_df
        price_data = [
            {"date": str(row["Date"])[:10], "close": round(row["Close"], 2)}
            for _, row in sampled.iterrows()
        ]

    chart_b64 = generate_sentiment_vs_price_chart(
        ticker=primary,
        quarterly_scores=quarterly_scores,
        price_data=price_data,
        competitors=competitor_signals if competitor_signals else None,
    )
    memo["chart_base64"] = chart_b64

    # Override recommendation/confidence with data-driven values (LLM tends to hardcode 75%)
    from tools.compute_signal import generate_recommendation
    computed_rec = generate_recommendation(
        language_signal=primary_language,
        market_signal=market_signal,
        competitor_signals=competitor_signals,
    )
    memo["recommendation"] = computed_rec["recommendation"]
    memo["signal"] = computed_rec["signal"]
    memo["confidence"] = computed_rec["confidence"]
    memo["language_trend"] = primary_language.get("trend", "unknown")
    memo["uncertainty_score_change"] = f"{primary_language.get('trend_magnitude', 0):+.1f}% vs prior quarter"

    # Compute comprehensive price statistics
    from tools.fetch_prices import compute_price_summary
    price_summary = compute_price_summary(primary, period="2y")
    comp_price_summaries = {}
    for c in competitor_signals:
        comp_ticker = c.get("company", "")
        if comp_ticker:
            comp_price_summaries[comp_ticker] = compute_price_summary(comp_ticker, period="2y")

    # Inject data sources so the frontend can link to raw data
    sources = {
        "primary": {
            "edgar_company_page": edgar_company_page,
            "filings": primary_filing_sources,
        },
        "competitors": {},
        "price_data": {
            "source": "Yahoo Finance",
            "ticker": primary,
            "url": f"https://finance.yahoo.com/quote/{primary}/history/",
            "summary": price_summary,
            "competitor_summaries": comp_price_summaries,
        },
        "raw_scores": {
            "primary_quarterly_scores": quarterly_scores,
            "competitor_quarterly_scores": {
                c.get("company", ""): c.get("quarterly_scores", [])
                for c in competitor_signals
            },
        },
    }
    # Add competitor filing sources
    for c in competitor_signals:
        comp_ticker = c.get("company", "")
        comp_sources = c.get("sources", {})
        if not comp_sources:
            # Build sources from quarterly_scores filing_urls if available
            comp_filings = []
            for q in c.get("quarterly_scores", []):
                if q.get("filing_url"):
                    comp_filings.append({
                        "period": q.get("period", ""),
                        "filing_date": q.get("filing_date", ""),
                        "form_type": form_type,
                        "url": q["filing_url"],
                    })
            comp_sources = {"filings": comp_filings}
        sources["competitors"][comp_ticker] = comp_sources
    memo["data_sources"] = sources

    yield {
        "type": "step",
        "agent": "AnalystAgent",
        "message": f"Analysis complete: {memo.get('recommendation', 'N/A')} ({memo.get('signal', 'N/A')}) with {int(memo.get('confidence', 0) * 100)}% confidence",
    }

    yield {"type": "result", "data": memo}
