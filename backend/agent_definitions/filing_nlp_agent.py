from agents import Agent, function_tool
from tools.fetch_filings import fetch_recent_filings, fetch_filing_text
from tools.analyze_language import analyze_filing_language, compute_trend
from schemas.language_signal import LanguageSignal


FILING_NLP_SYSTEM_PROMPT = """You are a specialized SEC filing language analyst. Your job is to:
1. Use the fetch_and_analyze_filings tool to retrieve and analyze recent SEC filings for the requested company.
2. Examine the results and provide your analysis as a structured LanguageSignal.

When the user gives you a ticker symbol and optionally a form type:
- Call the tool with those parameters
- The tool returns filing language analysis data
- Use that data to populate your structured output

Focus on whether management language is becoming more uncertain or more confident over time.
Always note the specific language shifts and what they might indicate about the company's outlook.
"""


@function_tool
def fetch_and_analyze_filings(
    ticker: str, form_type: str = "10-Q", num_quarters: int = 6
) -> str:
    """
    Fetch recent SEC filings for a ticker and analyze language trends.
    Returns JSON with quarterly language scores and trend analysis.

    Args:
        ticker: Stock ticker symbol (e.g. NVDA, AAPL)
        form_type: SEC form type - use 10-Q for quarterly, 10-K for annual
        num_quarters: Number of recent filings to analyze (default 6)
    """
    filings = fetch_recent_filings(ticker, form_type, num_quarters)
    if not filings:
        return f'{{"error": "No {form_type} filings found for {ticker}"}}'

    company_name = filings[0].get("company_name", ticker)
    quarterly_scores = []

    for filing in filings:
        text = fetch_filing_text(
            filing["accession_number"],
            filing["cik"],
            filing["primary_doc"],
        )
        if not text:
            continue

        score = analyze_filing_language(
            text, filing["period"], filing["filing_date"]
        )
        quarterly_scores.append(score)

    if not quarterly_scores:
        return f'{{"error": "Could not extract text from any filings for {ticker}"}}'

    trend_data = compute_trend(quarterly_scores)

    import json
    result = {
        "company": ticker.upper(),
        "company_name": company_name,
        "filings_analyzed": len(quarterly_scores),
        "quarterly_scores": quarterly_scores,
        "trend": trend_data["trend"],
        "trend_magnitude": trend_data["trend_magnitude"],
    }
    return json.dumps(result, indent=2)


filing_nlp_agent = Agent(
    name="FilingNLPAgent",
    instructions=FILING_NLP_SYSTEM_PROMPT,
    tools=[fetch_and_analyze_filings],
    output_type=LanguageSignal,
    model="gpt-4o",
)
