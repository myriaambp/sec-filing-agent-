from google.adk.agents import Agent
from tools.fetch_prices import fetch_price_history, compute_returns_around_date
from tools.compute_signal import correlate_language_with_returns, compute_signal_strength
import json


MARKET_SYSTEM_PROMPT = """You are a quantitative market signal analyst.

IMPORTANT: You MUST call the compute_market_signal tool first. Do NOT generate data from your own knowledge. The tool fetches real stock price data and computes correlations. If the tool returns an error, return that error as JSON: {"error": "message here"}.

Steps:
1. Call the compute_market_signal tool with the ticker, filing_dates, and uncertainty_scores provided.
2. Examine the tool's correlation data and assess signal strength.

Return your analysis as JSON matching this exact schema:

{
  "company": "TICKER",
  "correlations": [
    {
      "period": "2024-10",
      "uncertainty_score": 0.65,
      "return_30d": 0.05,
      "return_60d": 0.08,
      "sp500_return_30d": 0.03,
      "outperformed": true
    }
  ],
  "historical_accuracy": "description of predictive accuracy",
  "avg_30d_return_on_high_uncertainty": -0.02,
  "avg_30d_return_on_low_uncertainty": 0.06,
  "signal_strength": "strong",
  "summary": "2-3 sentence summary"
}

Focus on whether uncertainty in filings historically predicted stock underperformance.
Return ONLY the JSON, no other text.
"""


def compute_market_signal(
    ticker: str, filing_dates: list, uncertainty_scores: list
) -> str:
    """
    Compute whether filing language uncertainty predicted stock performance.
    Correlates uncertainty scores at each filing date with 30/60-day returns.

    Args:
        ticker: Stock ticker symbol (e.g. NVDA, AAPL)
        filing_dates: List of filing dates in YYYY-MM-DD format
        uncertainty_scores: List of uncertainty scores (0-1) matching the filing dates
    """
    price_df = fetch_price_history(ticker, period="3y")
    if price_df.empty:
        return json.dumps({"error": f"No price data found for {ticker}"})

    quarterly_scores = []
    price_returns = []
    for date_str, unc_score in zip(filing_dates, uncertainty_scores):
        quarterly_scores.append({
            "filing_date": date_str,
            "period": date_str[:7],
            "uncertainty_score": unc_score,
        })
        returns = compute_returns_around_date(
            ticker, date_str, windows=[30, 60], price_df=price_df
        )
        returns["filing_date"] = date_str
        price_returns.append(returns)

    correlations = correlate_language_with_returns(quarterly_scores, price_returns)
    signal = compute_signal_strength(correlations)

    result = {
        "company": ticker.upper(),
        "correlations": correlations,
        **signal,
    }
    return json.dumps(result, indent=2)


market_agent = Agent(
    model="gemini-2.0-flash",
    name="market_signal_agent",
    description="Analyzes stock price performance after SEC filings to find predictive signals from language uncertainty",
    instruction=MARKET_SYSTEM_PROMPT,
    tools=[compute_market_signal],
)
