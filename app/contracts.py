from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class NewsEvent(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    headline: str = Field(min_length=1, max_length=500)
    source: str = "manual"
    published_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SentimentScore(BaseModel):
    label: Literal["positive", "neutral", "negative"]
    score: float = Field(ge=-1, le=1)
    confidence: float = Field(ge=0, le=1)
    model_version: str


class RiskSnapshot(BaseModel):
    symbol: str
    event_id: str
    generated_at: datetime
    sentiment: SentimentScore
    expected_return: float
    volatility: float
    var_95: float
    cvar_95: float
    paths: int
    horizon_days: int
    distribution: list[float]
    degraded_components: list[str] = []
