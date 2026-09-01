import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.contracts import NewsEvent, RiskSnapshot
from app.events import EventBus
from app.pipeline import RiskPipeline
from app.risk import RiskEngine
from app.sentiment import HeuristicSentimentModel


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    bus = EventBus(settings.redis_url)
    await bus.connect()
    app.state.bus = bus
    app.state.pipeline = RiskPipeline(
        HeuristicSentimentModel(),
        RiskEngine(settings.simulation_paths, settings.simulation_horizon_days),
        bus,
    )
    yield
    await bus.close()


app = FastAPI(title="PulseRisk", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/events", response_model=RiskSnapshot)
async def process_event(event: NewsEvent) -> RiskSnapshot:
    return await app.state.pipeline.run(event)


@app.websocket("/v1/stream/{symbol}")
async def stream_symbol(websocket: WebSocket, symbol: str) -> None:
    await websocket.accept()
    try:
        async for message in app.state.bus.subscribe(f"risk:{symbol.upper()}"):
            await websocket.send_text(message)
    except (WebSocketDisconnect, asyncio.CancelledError):
        return
    except Exception as exc:  # noqa: BLE001 - report unexpected stream failures to the client.
        await websocket.send_text(json.dumps({"type": "stream_error", "detail": str(exc)}))
        await websocket.close(code=1011)
