from google.adk.agents import Agent
from utils.chart_generator import generate_sentiment_vs_price_chart
from tools.fetch_prices import fetch_price_history
from tools.compute_signal import generate_recommendation
import json


# Module-level storage for chart data (too large for LLM to pass through)
_last_chart_base64 = ""

ANALYST_SYSTEM_PROMPT = """You are a senior equity research analyst at a top-tier hedge fund. You synthesize SEC filing language analysis and market signal data into institutional-quality research memos.

You will receive language analysis and market signal data. You MUST call the generate_analyst_memo tool with all the data to get the recommendation and supporting evidence. Do NOT skip the tool call.

Then write your final output as JSON matching this exact schema:

{
  "company": "TICKER",
  "company_name": "Full Name",
  "competitors_analyzed": ["AMD", "INTC"],
  "recommendation": "BUY",
  "signal": "BULLISH",
  "confidence": 0.75,
  "language_trend": "improving",
  "uncertainty_score_change": "+23% vs last quarter",
  "key_evidence": ["evidence point 1", "evidence point 2", "evidence point 3"],
  "historical_context": "What happened last time the signal was similar",
  "competitor_comparison": "How language compares to peers",
  "full_memo": "Full markdown research memo...",
  "chart_base64": ""
}

IMPORTANT: Leave chart_base64 as an empty string "". The chart is injected separately.

For key_evidence, provide 4-6 specific data-backed points. Each should cite a number.

For historical_context, explain what happened to the stock in prior quarters when the language signal was similar. Cite specific returns.

For competitor_comparison, compare the primary company's uncertainty trend to each competitor with specific scores.

For full_memo, write a detailed Goldman Sachs-style research note in markdown with these sections:
## Investment Thesis
Why we are recommending this action. The core argument in 2-3 sentences.

## Language Trend Analysis
Quarter-by-quarter breakdown of uncertainty and sentiment scores. What specific shifts occurred and what they suggest about management's outlook.

## Market Signal Analysis
How has the stock historically performed after filings with similar language? Cite 30-day and 60-day returns. How does this compare to the S&P 500?

## Competitive Landscape
How does this company's filing language compare to peers? Who is trending better/worse and what does that imply?

## Risk Factors
What could invalidate this recommendation? What are the limitations of language-based analysis?

## Conclusion
Restate the recommendation with confidence level and the single most important data point supporting it.

Be specific. Cite numbers from the data. Do not be vague.
Return ONLY the JSON, no other text.
"""


def generate_analyst_memo(
    primary_ticker: str,
    primary_language_data: str,
    primary_market_data: str,
    competitor_language_data: str,
) -> str:
    """
    Synthesize language and market signals into a recommendation with chart.
    Returns JSON with recommendation, chart (base64 PNG), and supporting data.

    Args:
        primary_ticker: The main company ticker
        primary_language_data: JSON string of language analysis data for primary company
        primary_market_data: JSON string of market signal data for primary company
        competitor_language_data: JSON string of list of competitor language analysis data
    """
    try:
        lang_data = json.loads(primary_language_data)
    except (json.JSONDecodeError, TypeError):
        lang_data = {}

    try:
        market_data = json.loads(primary_market_data)
    except (json.JSONDecodeError, TypeError):
        market_data = {}

    try:
        comp_data = json.loads(competitor_language_data)
    except (json.JSONDecodeError, TypeError):
        comp_data = []

    rec = generate_recommendation(
        language_signal=lang_data,
        market_signal=market_data,
        competitor_signals=comp_data,
    )

    quarterly_scores = lang_data.get("quarterly_scores", [])
    price_df = fetch_price_history(primary_ticker, period="2y")
    price_data = []
    if not price_df.empty:
        sampled = price_df.iloc[::5] if len(price_df) > 50 else price_df
        price_data = [
            {"date": str(row["Date"])[:10], "close": round(row["Close"], 2)}
            for _, row in sampled.iterrows()
        ]

    chart_b64 = generate_sentiment_vs_price_chart(
        ticker=primary_ticker,
        quarterly_scores=quarterly_scores,
        price_data=price_data,
        competitors=comp_data if comp_data else None,
    )

    # Store chart in module-level variable (too large for LLM context)
    global _last_chart_base64
    _last_chart_base64 = chart_b64

    result = {
        "recommendation": rec["recommendation"],
        "signal": rec["signal"],
        "confidence": rec["confidence"],
        "language_trend": lang_data.get("trend", "unknown"),
        "trend_magnitude": lang_data.get("trend_magnitude", 0),
        "competitor_tickers": [c.get("company", "") for c in comp_data] if comp_data else [],
    }
    return json.dumps(result, indent=2)


analyst_agent = Agent(
    model="gemini-2.0-flash",
    name="analyst_agent",
    description="Synthesizes filing language and market signal analyses into a structured research memo with Buy/Sell/Hold recommendation",
    instruction=ANALYST_SYSTEM_PROMPT,
    tools=[generate_analyst_memo],
)
