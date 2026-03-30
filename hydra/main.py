import asyncio
import redis as redis_lib
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request

from hydra.config.settings import get_settings
from hydra.config.markets import MarketManager
from hydra.config.keys import KeyManager
from hydra.core.kill_switch import KillSwitch
from hydra.core.order_queue import OrderQueue
from hydra.core.position_tracker import PositionTracker
from hydra.core.pnl_tracker import PnlTracker
from hydra.core.risk_engine import RiskEngine
from hydra.core.state_manager import StateManager
from hydra.exchange.factory import create_exchanges
from hydra.logging.setup import configure_logging, get_logger
from hydra.notify.telegram import TelegramNotifier
from hydra.resilience.graceful import GracefulManager

from hydra.api import health, orders, positions, risk, markets, system, strategies, pnl as pnl_api
from hydra.api.health import set_redis
from hydra.api.orders import set_order_queue
from hydra.api.positions import set_position_tracker
from hydra.api.risk import set_dependencies as set_risk_deps
from hydra.api.markets import set_market_manager
from hydra.api.pnl import set_pnl_dependencies
from hydra.api import data as data_api
from hydra.api.data import set_store
from hydra.api import indicators as indicators_api
from hydra.api.indicators import set_redis_for_indicators
from hydra.api import regime as regime_api
from hydra.api.regime import set_redis_for_regime
from hydra.api import signals as signals_api
from hydra.api.signals import set_redis_for_signals
from hydra.api import supplemental as supplemental_api
from hydra.api.supplemental import set_redis_for_supplemental
from hydra.api import backtest as backtest_api
from hydra.api.backtest import set_store_for_backtest
from hydra.data.storage import create_store

logger = get_logger(__name__)
KILL_BLOCKED_KEY = "hydra:kill_switch_active"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("hydra_starting", profile=settings.hydra_profile)

    r = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
    set_redis(r)

    market_manager = MarketManager()
    key_manager = KeyManager()
    telegram = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)
    position_tracker = PositionTracker(r)
    state_manager = StateManager(r)
    risk_engine = RiskEngine(r, position_tracker)
    pnl_tracker = PnlTracker(r)
    ohlcv_store = create_store()
    await ohlcv_store.init()
    exchanges = create_exchanges(market_manager, key_manager)

    kill_switch = KillSwitch(
        exchanges=exchanges,
        position_tracker=position_tracker,
        telegram=telegram,
        redis_client=r,
    )
    order_queue = OrderQueue(
        redis_client=r,
        risk_engine=risk_engine,
        position_tracker=position_tracker,
        exchanges=exchanges,
    )
    graceful = GracefulManager(order_queue, position_tracker, r)
    graceful.register_signals()

    set_order_queue(order_queue)
    set_position_tracker(position_tracker)
    set_risk_deps(kill_switch, risk_engine)
    set_market_manager(market_manager)
    set_pnl_dependencies(pnl_tracker, position_tracker)
    set_store(ohlcv_store)
    set_redis_for_indicators(r)
    set_redis_for_regime(r)
    set_redis_for_signals(r)
    set_redis_for_supplemental(r)
    set_store_for_backtest(ohlcv_store)

    logger.info("hydra_started")
    try:
        yield
    finally:
        logger.info("hydra_stopping")
        await ohlcv_store.close()


def create_app() -> FastAPI:
    app = FastAPI(title="HYDRA", version="0.1.0", docs_url=None, redoc_url=None, lifespan=lifespan)

    @app.middleware("http")
    async def auth_guard(request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        return await call_next(request)

    app.include_router(health.router)
    app.include_router(orders.router)
    app.include_router(positions.router)
    app.include_router(risk.router)
    app.include_router(markets.router)
    app.include_router(system.router)
    app.include_router(strategies.router)
    app.include_router(pnl_api.router)
    app.include_router(data_api.router)
    app.include_router(indicators_api.router)
    app.include_router(regime_api.router)
    app.include_router(signals_api.router)
    app.include_router(supplemental_api.router)
    app.include_router(backtest_api.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hydra.main:app", host="127.0.0.1", port=8000, reload=False)
