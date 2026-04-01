from agents import Agent, function_tool
from tools.fetch_prices import fetch_price_history, compute_returns_around_date
from tools.compute_signal import correlate_language_with_returns, compute_signal_strength
from schemas.market_signal import MarketSignal
import json


MARKET_SYSTEM_PROMPT = """You are a quantitative market signal analyst. Your job is to:
1. Use the compute_market_signal tool to analyze how a company's stock performed after each SEC filing.
2. The tool correlates filing language uncertainty scores with subsequent stock returns.
3. Use the results to populate your structured MarketSignal output.

When given a ticker, filing dates, and uncertainty scores:
- Call the tool with those parameters
- Examine the correlation data
- Determine if uncertainty in filings has historically predicted stock underperformance
- Assess the signal strength (strong, moderate, or weak)

Focus on whether the relationship is consistent enough to be actionable.
"""


@function_tool
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

    # Build quarterly scores and price returns
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
    name="MarketSignalAgent",
    instructions=MARKET_SYSTEM_PROMPT,
    tools=[compute_market_signal],
    output_type=MarketSignal,
    model="gpt-4o",
)
