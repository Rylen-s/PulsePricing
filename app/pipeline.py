import asyncio
import uuid
from datetime import UTC, datetime
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.contracts import NewsEvent, RiskSnapshot, SentimentScore
from app.events import EventBus
from app.risk import RiskEngine
from app.sentiment import SentimentModel


class PipelineState(TypedDict, total=False):
    event: NewsEvent
    event_id: str
    sentiment: SentimentScore
    risk: dict
    degraded_components: list[str]


class RiskPipeline:
    def __init__(self, model: SentimentModel, engine: RiskEngine, bus: EventBus):
        self.model, self.engine, self.bus = model, engine, bus
        self.graph = self._build_graph()

    def _build_graph(self):
        async def score(state: PipelineState) -> dict:
            try:
                return {"sentiment": await self.model.score(state["event"].headline)}
            except Exception:  # noqa: BLE001 - model failure must degrade to a neutral score.
                return {
                    "sentiment": SentimentScore(
                        label="neutral", score=0, confidence=0, model_version="fallback-v0"
                    ),
                    "degraded_components": ["sentiment"],
                }

        async def simulate(state: PipelineState) -> dict:
            try:
                risk = await asyncio.to_thread(self.engine.simulate, state["sentiment"])
                return {"risk": risk}
            except Exception:  # noqa: BLE001 - a failed run must still publish a safe snapshot.
                return {
                    "risk": {
                        "expected_return": 0,
                        "volatility": 0,
                        "var_95": 0,
                        "cvar_95": 0,
                        "distribution": [],
                    },
                    "degraded_components": state.get("degraded_components", []) + ["risk"],
                }

        graph = StateGraph(PipelineState)
        graph.add_node("score_sentiment", score)
        graph.add_node("simulate_risk", simulate)
        graph.add_edge(START, "score_sentiment")
        graph.add_edge("score_sentiment", "simulate_risk")
        graph.add_edge("simulate_risk", END)
        return graph.compile()

    async def run(self, event: NewsEvent) -> RiskSnapshot:
        state = await self.graph.ainvoke(
            {"event": event, "event_id": str(uuid.uuid4()), "degraded_components": []}
        )
        risk = state["risk"]
        snapshot = RiskSnapshot(
            symbol=event.symbol.upper(),
            event_id=state["event_id"],
            generated_at=datetime.now(UTC),
            sentiment=state["sentiment"],
            paths=self.engine.paths,
            horizon_days=self.engine.horizon_days,
            degraded_components=state.get("degraded_components", []),
            **risk,
        )
        await self.bus.publish(f"risk:{snapshot.symbol}", snapshot.model_dump(mode="json"))
        return snapshot
