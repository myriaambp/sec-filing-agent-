from google.adk.agents import Agent
from tools.fetch_filings import fetch_recent_filings, fetch_filing_text
from tools.analyze_language import analyze_filing_language, compute_trend
import json


FILING_NLP_SYSTEM_PROMPT = """You are a specialized SEC filing language analyst. Your job is to:
1. Use the fetch_and_analyze_filings tool to retrieve and analyze recent SEC filings for the requested company.
2. Examine the results carefully.
3. Return your analysis as JSON matching this exact schema:

{
  "company": "TICKER",
  "company_name": "Full Company Name",
  "filings_analyzed": 4,
  "quarterly_scores": [
    {
      "period": "2024-10-27",
      "filing_date": "2024-11-19",
      "uncertainty_score": 0.65,
      "sentiment_score": -0.3,
      "uncertainty_word_count": 37,
      "total_word_count": 2100,
      "key_risk_phrases": ["phrase 1", "phrase 2"]
    }
  ],
  "trend": "deteriorating",
  "trend_magnitude": 13.5,
  "summary": "2-3 sentence summary of language trend"
}

Focus on whether management language is becoming more uncertain or more confident over time.
Always note the specific language shifts and what they might indicate.
Return ONLY the JSON, no other text.
"""


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
        return json.dumps({"error": f"No {form_type} filings found for {ticker}"})

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
        return json.dumps({"error": f"Could not extract text from any filings for {ticker}"})

    trend_data = compute_trend(quarterly_scores)

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
    model="gemini-2.0-flash",
    name="filing_nlp_agent",
    description="Fetches and analyzes SEC filing language for a company to detect uncertainty trends",
    instruction=FILING_NLP_SYSTEM_PROMPT,
    tools=[fetch_and_analyze_filings],
)
