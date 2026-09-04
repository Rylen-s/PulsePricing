from app.contracts import SentimentScore
from app.risk import RiskEngine


def test_simulation_has_expected_shape_and_risk_ordering():
    engine = RiskEngine(paths=2_000, horizon_days=50)
    result = engine.simulate(
        SentimentScore(label="neutral", score=0, confidence=1, model_version="test"), seed=7
    )
    assert len(result["distribution"]) == 99
    assert result["cvar_95"] >= result["var_95"] >= 0
