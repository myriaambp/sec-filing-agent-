from pydantic import BaseModel
from typing import List


class QuarterlyLanguageScore(BaseModel):
    period: str
    filing_date: str
    uncertainty_score: float
    sentiment_score: float
    uncertainty_word_count: int
    total_word_count: int
    key_risk_phrases: List[str]


class LanguageSignal(BaseModel):
    company: str
    company_name: str
    filings_analyzed: int
    quarterly_scores: List[QuarterlyLanguageScore]
    trend: str
    trend_magnitude: float
    summary: str
