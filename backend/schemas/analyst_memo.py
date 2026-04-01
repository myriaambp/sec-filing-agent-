from pydantic import BaseModel
from typing import List


class AnalystMemo(BaseModel):
    company: str
    company_name: str
    competitors_analyzed: List[str]
    recommendation: str
    signal: str
    confidence: float
    language_trend: str
    uncertainty_score_change: str
    key_evidence: List[str]
    historical_context: str
    competitor_comparison: str
    full_memo: str
    chart_base64: str
