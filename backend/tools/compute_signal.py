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
    Confidence is computed from multiple factors rather than hardcoded.
    """
    trend = language_signal.get("trend", "stable")
    strength = market_signal.get("signal_strength", "weak")
    trend_mag = language_signal.get("trend_magnitude", 0.0)

    # --- Determine recommendation direction ---
    if trend == "deteriorating" and strength in ("strong", "moderate"):
        if abs(trend_mag) > 20:
            rec = "SELL"
            signal = "BEARISH"
        else:
            rec = "UNDERWEIGHT"
            signal = "CAUTIONARY"
    elif trend == "improving" and strength in ("strong", "moderate"):
        if abs(trend_mag) > 20:
            rec = "BUY"
            signal = "BULLISH"
        else:
            rec = "OVERWEIGHT"
            signal = "BULLISH"
    else:
        rec = "HOLD"
        signal = "CAUTIONARY"

    # --- Compute confidence from data factors ---
    confidence = 0.30  # base

    # Factor 1: Signal strength from market correlation (0-0.20)
    strength_bonus = {"strong": 0.20, "moderate": 0.12, "weak": 0.04}
    confidence += strength_bonus.get(strength, 0.0)

    # Factor 2: Trend magnitude — bigger shift = more confident (0-0.15)
    mag_bonus = min(0.15, abs(trend_mag) / 200)
    confidence += mag_bonus

    # Factor 3: Number of filings analyzed — more data = more confident (0-0.10)
    quarterly_scores = language_signal.get("quarterly_scores", [])
    if not quarterly_scores:
        # Fallback: check filings_analyzed count from language_signal dict
        n_filings = language_signal.get("filings_analyzed", 0)
    else:
        n_filings = len(quarterly_scores)
    filings_bonus = min(0.10, n_filings * 0.02)
    confidence += filings_bonus

    # Factor 4: Trend consistency — are scores moving in same direction? (0-0.10)
    if len(quarterly_scores) >= 3:
        scores = [q.get("uncertainty_score", 0) for q in sorted(
            quarterly_scores, key=lambda x: x.get("filing_date", "")
        )]
        # Check if scores are monotonically increasing/decreasing
        diffs = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
        if all(d > 0 for d in diffs) or all(d < 0 for d in diffs):
            confidence += 0.10  # perfectly consistent trend
        elif sum(1 for d in diffs if d > 0) >= len(diffs) * 0.7 or \
             sum(1 for d in diffs if d < 0) >= len(diffs) * 0.7:
            confidence += 0.05  # mostly consistent

    # Factor 5: Return spread between high/low uncertainty (0-0.10)
    avg_high = market_signal.get("avg_30d_return_on_high_uncertainty", 0)
    avg_low = market_signal.get("avg_30d_return_on_low_uncertainty", 0)
    spread = abs(avg_high - avg_low)
    spread_bonus = min(0.10, spread * 1.0)
    confidence += spread_bonus

    # Factor 6: Competitor divergence bonus (0-0.05)
    if competitor_signals:
        comp_trends = [c.get("trend", "stable") for c in competitor_signals]
        if trend == "deteriorating" and all(t != "deteriorating" for t in comp_trends):
            confidence += 0.05
        elif trend == "improving" and all(t != "improving" for t in comp_trends):
            confidence += 0.05

    # Clamp to 0.15-0.95 range
    confidence = max(0.15, min(0.95, confidence))

    return {
        "recommendation": rec,
        "signal": signal,
        "confidence": round(confidence, 2),
    }
