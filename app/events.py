import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator


class EventBus:
    """Redis pub/sub with an in-memory fallback suitable for one local process."""

    def __init__(self, redis_url: str | None):
        self.redis_url = redis_url
        self._redis = None
        self._channels: dict[str, set[asyncio.Queue[str]]] = defaultdict(set)

    async def connect(self) -> None:
        if not self.redis_url:
            return
        try:
            from redis.asyncio import Redis

            self._redis = Redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()
        except Exception:  # noqa: BLE001 - Redis is explicitly optional in local mode.
            self._redis = None

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    async def publish(self, topic: str, payload: dict) -> None:
        message = json.dumps(payload, default=str)
        if self._redis:
            await self._redis.publish(topic, message)
            return
        for queue in list(self._channels[topic]):
            queue.put_nowait(message)

    async def subscribe(self, topic: str) -> AsyncIterator[str]:
        if self._redis:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(topic)
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield message["data"]
            finally:
                await pubsub.unsubscribe(topic)
                await pubsub.aclose()
            return
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
        self._channels[topic].add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._channels[topic].discard(queue)
