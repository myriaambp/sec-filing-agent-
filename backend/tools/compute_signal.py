from typing import List, Dict
import numpy as np


def correlate_language_with_returns(
    quarterly_scores: List[Dict],
    price_returns: List[Dict],
) -> List[Dict]:
    """
    Join language scores with 30/60-day returns for each quarter.
    Returns list of FilingReturnCorrelation dicts.
    """
    correlations = []
    scores_by_date = {s["filing_date"]: s for s in quarterly_scores}

    for ret in price_returns:
        filing_date = ret.get("filing_date", "")
        score = scores_by_date.get(filing_date)
        if not score:
            continue
        correlations.append({
            "period": score.get("period", ""),
            "uncertainty_score": score["uncertainty_score"],
            "return_30d": ret.get("return_30d", 0.0),
            "return_60d": ret.get("return_60d", 0.0),
            "sp500_return_30d": ret.get("sp500_return_30d", 0.0),
            "outperformed": ret.get("outperformed_30d", False),
        })

    return correlations


def compute_signal_strength(correlations: List[Dict]) -> Dict:
    """
    Analyze the historical relationship between uncertainty and returns.
    """
    if not correlations:
        return {
            "signal_strength": "insufficient_data",
            "avg_30d_return_on_high_uncertainty": 0.0,
            "avg_30d_return_on_low_uncertainty": 0.0,
            "historical_accuracy": "Insufficient data to compute signal.",
        }

    unc_scores = [c["uncertainty_score"] for c in correlations]
    median_unc = float(np.median(unc_scores)) if unc_scores else 0.5

    high_unc = [c for c in correlations if c["uncertainty_score"] >= median_unc]
    low_unc = [c for c in correlations if c["uncertainty_score"] < median_unc]

    avg_high = (
        np.mean([c["return_30d"] for c in high_unc]) if high_unc else 0.0
    )
    avg_low = (
        np.mean([c["return_30d"] for c in low_unc]) if low_unc else 0.0
    )

    # How often did high uncertainty predict underperformance?
    if high_unc:
        underperform_count = sum(
            1 for c in high_unc if not c["outperformed"]
        )
        accuracy = underperform_count / len(high_unc)
    else:
        accuracy = 0.0

    spread = abs(avg_high - avg_low)
    if spread > 0.05 and accuracy > 0.6:
        strength = "strong"
    elif spread > 0.02 or accuracy > 0.5:
        strength = "moderate"
    else:
        strength = "weak"

    n_high = len(high_unc)
    n_cases = len(correlations)
    accuracy_str = (
        f"When uncertainty was above median, the stock underperformed the S&P 500 "
        f"in {int(accuracy * 100)}% of cases ({n_high} of {n_cases} quarters analyzed)."
    )

    return {
        "signal_strength": strength,
        "avg_30d_return_on_high_uncertainty": round(float(avg_high), 4),
        "avg_30d_return_on_low_uncertainty": round(float(avg_low), 4),
        "historical_accuracy": accuracy_str,
    }


def generate_recommendation(
    language_signal: Dict,
    market_signal: Dict,
    competitor_signals: List[Dict],
) -> Dict:
    """
    Synthesize all signals into a recommendation.
    """
    trend = language_signal.get("trend", "stable")
    strength = market_signal.get("signal_strength", "weak")
    trend_mag = language_signal.get("trend_magnitude", 0.0)

    # Core logic
    if trend == "deteriorating" and strength in ("strong", "moderate"):
        if abs(trend_mag) > 20:
            rec = "SELL"
            signal = "BEARISH"
            confidence = 0.75
        else:
            rec = "UNDERWEIGHT"
            signal = "CAUTIONARY"
            confidence = 0.60
    elif trend == "improving" and strength in ("strong", "moderate"):
        if abs(trend_mag) > 20:
            rec = "BUY"
            signal = "BULLISH"
            confidence = 0.75
        else:
            rec = "OVERWEIGHT"
            signal = "BULLISH"
            confidence = 0.60
    else:
        rec = "HOLD"
        signal = "CAUTIONARY"
        confidence = 0.45

    # Adjust confidence based on competitor comparison
    if competitor_signals:
        comp_trends = [c.get("trend", "stable") for c in competitor_signals]
        if trend == "deteriorating" and all(t != "deteriorating" for t in comp_trends):
            confidence = min(1.0, confidence + 0.10)
        elif trend == "improving" and all(t != "improving" for t in comp_trends):
            confidence = min(1.0, confidence + 0.10)

    return {
        "recommendation": rec,
        "signal": signal,
        "confidence": round(confidence, 2),
    }
