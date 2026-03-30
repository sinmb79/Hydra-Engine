from hydra.config.markets import MarketManager
from hydra.config.keys import KeyManager
from hydra.exchange.base import BaseExchange
from hydra.exchange.crypto import CryptoExchange
from hydra.exchange.kis import KISExchange
from hydra.exchange.polymarket import PolymarketExchange
from hydra.logging.setup import get_logger

logger = get_logger(__name__)


def create_exchanges(market_manager: MarketManager, key_manager: KeyManager) -> dict[str, BaseExchange]:
    """활성화된 시장의 거래소 커넥터만 생성."""
    exchanges: dict[str, BaseExchange] = {}
    active = market_manager.get_active_markets()

    for market in active:
        mode = market_manager.get_mode(market)
        is_paper = mode == "paper"
        try:
            if market == "kr":
                app_key, secret = key_manager.load("kis_kr")
                account_no, _ = key_manager.load("kis_account")
                exchanges["kr"] = KISExchange(app_key, secret, account_no, is_paper=is_paper)
            elif market == "us":
                app_key, secret = key_manager.load("kis_us")
                account_no, _ = key_manager.load("kis_account")
                exchanges["us"] = KISExchange(app_key, secret, account_no, is_paper=is_paper)
            elif market == "upbit":
                exchanges["upbit"] = CryptoExchange("upbit")
            elif market == "binance":
                exchanges["binance"] = CryptoExchange("binance")
            elif market == "hl":
                exchanges["hl"] = CryptoExchange("hyperliquid")
            elif market == "poly":
                exchanges["poly"] = PolymarketExchange()
            logger.info("exchange_created", market=market, mode=mode)
        except Exception as e:
            logger.error("exchange_create_failed", market=market, error=str(e))

    return exchanges
