from pydantic import BaseModel
from typing import List


class FilingReturnCorrelation(BaseModel):
    period: str
    uncertainty_score: float
    return_30d: float
    return_60d: float
    sp500_return_30d: float
    outperformed: bool


class MarketSignal(BaseModel):
    company: str
    correlations: List[FilingReturnCorrelation]
    historical_accuracy: str
    avg_30d_return_on_high_uncertainty: float
    avg_30d_return_on_low_uncertainty: float
    signal_strength: str
    summary: str
