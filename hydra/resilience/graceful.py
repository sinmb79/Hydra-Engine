import asyncio
import signal

from hydra.logging.setup import get_logger

logger = get_logger(__name__)
_SHUTDOWN_TIMEOUT = 30


class GracefulManager:
    def __init__(self, order_queue, position_tracker, redis_client):
        self._order_queue = order_queue
        self._positions = position_tracker
        self._redis = redis_client
        self._shutting_down = False

    def register_signals(self) -> None:
        """메인 이벤트 루프에서 호출. SIGTERM/SIGINT 핸들러 등록."""
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s.name)))

    async def shutdown(self, reason: str = "unknown") -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        logger.info("graceful_shutdown_start", reason=reason)
        try:
            async with asyncio.timeout(_SHUTDOWN_TIMEOUT):
                self._order_queue.block_new_orders()
                snapshot = await self._positions.snapshot()
                self._redis.set("hydra:last_snapshot", str(snapshot))
                logger.info("graceful_shutdown_complete")
        except TimeoutError:
            logger.error("graceful_shutdown_timeout", seconds=_SHUTDOWN_TIMEOUT)
