from typing import ClassVar, Protocol

from app.contracts import SentimentScore


class SentimentModel(Protocol):
    async def score(self, text: str) -> SentimentScore: ...


class HeuristicSentimentModel:
    """Deterministic local baseline; replace with versioned FinBERT/LSTM serving."""

    positive: ClassVar[set[str]] = {
        "rally",
        "beats",
        "growth",
        "surge",
        "approval",
        "strong",
        "encouraging",
    }
    negative: ClassVar[set[str]] = {
        "plunge",
        "misses",
        "fraud",
        "downgrade",
        "recession",
        "weak",
        "risk",
    }

    async def score(self, text: str) -> SentimentScore:
        words = set(text.lower().replace(".", "").replace(",", "").split())
        raw = len(words & self.positive) - len(words & self.negative)
        score = max(-1.0, min(1.0, raw / 3))
        label = "positive" if score > 0.15 else "negative" if score < -0.15 else "neutral"
        return SentimentScore(
            label=label,
            score=score,
            confidence=min(0.9, 0.45 + abs(score) * 0.4),
            model_version="heuristic-v0",
        )
