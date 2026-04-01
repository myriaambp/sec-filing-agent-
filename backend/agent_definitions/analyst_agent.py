from agents import Agent, function_tool
from utils.chart_generator import generate_sentiment_vs_price_chart
from tools.fetch_prices import fetch_price_history
from schemas.analyst_memo import AnalystMemo
from tools.compute_signal import generate_recommendation
import json


ANALYST_SYSTEM_PROMPT = """You are a senior equity research analyst at a top-tier hedge fund. You synthesize SEC filing language analysis and market signal data into institutional-quality research memos.

You will receive:
1. Language analysis data for a primary company (and possibly competitors)
2. Market signal data showing how filing language historically correlated with stock returns

Your job:
1. Call the generate_analyst_memo tool with all the data you received
2. Use the tool's output (recommendation, chart, evidence) to write your structured AnalystMemo

Write in the style of a Goldman Sachs or Morgan Stanley equity research note.
Be specific. Cite numbers. Do not be vague.

Your full_memo field should be a complete markdown-formatted research memo including:
- Opening recommendation with confidence level
- Language trend analysis with specific scores
- Historical signal analysis
- Competitor comparison
- Risk factors
- Conclusion with clear "so what" for a portfolio manager
"""


@function_tool
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
        primary_language_data: JSON string of LanguageSignal data for primary company
        primary_market_data: JSON string of MarketSignal data for primary company
        competitor_language_data: JSON string of list of competitor LanguageSignal data
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

    # Generate recommendation
    rec = generate_recommendation(
        language_signal=lang_data,
        market_signal=market_data,
        competitor_signals=comp_data,
    )

    # Generate chart
    quarterly_scores = lang_data.get("quarterly_scores", [])
    price_df = fetch_price_history(primary_ticker, period="2y")
    price_data = []
    if not price_df.empty:
        # Sample weekly for chart readability
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

    result = {
        "recommendation": rec["recommendation"],
        "signal": rec["signal"],
        "confidence": rec["confidence"],
        "chart_base64": chart_b64,
        "language_trend": lang_data.get("trend", "unknown"),
        "trend_magnitude": lang_data.get("trend_magnitude", 0),
        "competitor_tickers": [c.get("company", "") for c in comp_data] if comp_data else [],
    }
    return json.dumps(result, indent=2)


analyst_agent = Agent(
    name="AnalystAgent",
    instructions=ANALYST_SYSTEM_PROMPT,
    tools=[generate_analyst_memo],
    output_type=AnalystMemo,
    model="gpt-4o",
)
