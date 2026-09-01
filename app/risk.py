import numpy as np

from app.contracts import SentimentScore


class RiskEngine:
    """Stable Python reference implementation for the future C++ engine contract."""

    def __init__(self, paths: int, horizon_days: int):
        self.paths, self.horizon_days = paths, horizon_days

    def simulate(self, sentiment: SentimentScore, seed: int | None = None) -> dict:
        rng = np.random.default_rng(seed)
        dt = self.horizon_days / 252
        # Sentiment is a bounded, transparent adjustment—not a trading signal.
        drift = 0.08 + 0.10 * sentiment.score
        volatility = 0.20 * (1 + 0.20 * max(-sentiment.score, 0))
        jumps = rng.poisson(0.30 * dt, self.paths) * rng.normal(-0.04, 0.08, self.paths)
        log_returns = (
            (drift - 0.5 * volatility**2) * dt
            + volatility * np.sqrt(dt) * rng.normal(size=self.paths)
            + jumps
        )
        returns = np.expm1(log_returns)
        losses = -returns
        cutoff = np.quantile(losses, 0.95)
        return {
            "expected_return": float(np.mean(returns)),
            "volatility": float(np.std(returns)),
            "var_95": float(cutoff),
            "cvar_95": float(np.mean(losses[losses >= cutoff])),
            "distribution": np.quantile(returns, np.linspace(0.01, 0.99, 99)).round(7).tolist(),
        }
