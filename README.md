# PulseRisk

PulseRisk is a pragmatic foundation for a real-time, sentiment-driven risk simulator. The first release prioritizes the live path:

`market/news event -> resilient sentiment pipeline -> jump-diffusion Monte Carlo -> Redis -> WebSocket clients`

It deliberately keeps quant extensions (options Greeks, factor models, technical indicators, optimization, and RL) outside the critical path. Every external provider and model is behind a small interface so a free local demo works without API keys, while production providers can be enabled through environment variables.

## Stack and deployment shape

| Concern | Choice | Why |
| --- | --- | --- |
| API / realtime | FastAPI + WebSockets | Async, typed API surface and a single low-cost service. |
| Orchestration | LangGraph | Per-node fallbacks make a failed provider/model non-fatal. |
| Simulation | NumPy now; C++/pybind11 seam later | Gets a testable vertical slice running today while retaining a native-core contract. |
| Event fan-out / cache | Redis | Pub/sub for distribution updates and low-latency cache keys. |
| System of record | PostgreSQL | Profiles, strategies, snapshots and backtests when persistence is enabled. |
| UI | Separate Vercel-hosted React/Three.js client | Browsers subscribe directly to the API WebSocket; no server-side visualization work. |

For a cheap first deployment, run the API on Railway/Fly.io/Render, use Upstash Redis and Neon/Supabase Postgres, and deploy the UI to Vercel. Do not use Vercel serverless functions for the long-lived WebSocket/API worker.

## Quick start

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/health
curl -X POST http://localhost:8000/v1/events \
  -H 'content-type: application/json' \
  -d '{"symbol":"SPY","headline":"Markets rally after encouraging inflation data","source":"demo"}'
```

Open `ws://localhost:8000/v1/stream/SPY` in a WebSocket client before posting an event to receive the distribution update. The app falls back to an in-process bus if Redis is not available, so `uv run uvicorn app.main:app --reload` also works locally.

## Production next increments

1. Replace `HeuristicSentimentModel` with a batch FinBERT inference service (ONNX Runtime for CPU, Triton/CUDA where justified); train the temporal model independently and version both artifacts.
2. Add Alpha Vantage polling with rate limiting and a licensed news/RSS adapter. CNBC's terms and feed availability must be reviewed before production ingestion—never scrape a site by default.
3. Compile `native/monte_carlo` as a pybind11 extension and preserve the `RiskEngine.simulate` response contract.
4. Add Alembic migrations, auth, durable jobs, idempotency/event deduplication, observability, and load tests before claiming latency targets.

Latency targets such as “under 100 ms” must be measured end-to-end per provider/model/hardware; they are not properties of this scaffold.
