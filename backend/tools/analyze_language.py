import re
from typing import List, Dict

UNCERTAINTY_WORDS = [
    "may", "might", "could", "uncertain", "uncertainty", "risk", "risks",
    "headwinds", "challenging", "difficult", "adverse", "unfavorable",
    "decline", "decrease", "volatility", "unpredictable", "fluctuation",
    "concern", "concerns", "exposure", "susceptible", "dependent",
    "impairment", "litigation", "downturn", "weakening", "deterioration",
]

CONFIDENCE_WORDS = [
    "strong", "growth", "increase", "opportunity", "momentum", "confident",
    "outperform", "leadership", "advantage", "innovation", "expanding",
    "accelerating", "robust", "record", "exceeded", "surpassed",
    "improved", "favorable", "strength", "positive", "optimistic",
]


def count_words(text: str) -> Dict:
    """Count uncertainty and confidence word occurrences."""
    words = re.findall(r"\b[a-z]+\b", text.lower())
    total = len(words) if words else 1

    uncertainty_count = sum(1 for w in words if w in UNCERTAINTY_WORDS)
    confidence_count = sum(1 for w in words if w in CONFIDENCE_WORDS)

    return {
        "uncertainty_count": uncertainty_count,
        "confidence_count": confidence_count,
        "total_words": total,
        "uncertainty_ratio": round(uncertainty_count / total, 6),
        "confidence_ratio": round(confidence_count / total, 6),
    }


def compute_sentiment_score(text: str) -> float:
    """
    Sentiment: (confidence - uncertainty) / total * 1000.
    Normalized roughly to -1.0 to 1.0 range.
    """
    counts = count_words(text)
    raw = (counts["confidence_count"] - counts["uncertainty_count"]) / counts["total_words"]
    # Scale up and clamp
    score = max(-1.0, min(1.0, raw * 50))
    return round(score, 4)


def compute_uncertainty_score(text: str) -> float:
    """Uncertainty score: ratio of uncertainty words, scaled to 0-1."""
    counts = count_words(text)
    # Typical SEC filing uncertainty ratio is 0.005 - 0.025
    # Scale so 0.005 -> ~0.2 and 0.025 -> ~1.0
    score = min(1.0, counts["uncertainty_ratio"] * 40)
    return round(score, 4)


def extract_key_risk_phrases(text: str, n: int = 5) -> List[str]:
    """Extract sentences with highest density of uncertainty words."""
    sentences = re.split(r"[.!?]+", text)
    scored = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 30 or len(sent) > 500:
            continue
        words = re.findall(r"\b[a-z]+\b", sent.lower())
        if not words:
            continue
        unc_count = sum(1 for w in words if w in UNCERTAINTY_WORDS)
        if unc_count >= 2:
            scored.append((unc_count / len(words), sent.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:n]]


def analyze_filing_language(text: str, period: str, filing_date: str) -> Dict:
    """Run all analysis on a single filing's text."""
    return {
        "period": period,
        "filing_date": filing_date,
        "uncertainty_score": compute_uncertainty_score(text),
        "sentiment_score": compute_sentiment_score(text),
        "uncertainty_word_count": count_words(text)["uncertainty_count"],
        "total_word_count": count_words(text)["total_words"],
        "key_risk_phrases": extract_key_risk_phrases(text),
    }


def compute_trend(quarterly_scores: List[Dict]) -> Dict:
    """
    Compute trend direction and magnitude across quarters.
    """
    if len(quarterly_scores) < 2:
        return {"trend": "insufficient_data", "trend_magnitude": 0.0}

    scores = sorted(quarterly_scores, key=lambda x: x["filing_date"])
    recent = scores[-1]["uncertainty_score"]
    previous = scores[-2]["uncertainty_score"]

    if previous == 0:
        change_pct = 0.0
    else:
        change_pct = ((recent - previous) / previous) * 100

    if change_pct > 10:
        trend = "deteriorating"
    elif change_pct < -10:
        trend = "improving"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "trend_magnitude": round(change_pct, 2),
    }
