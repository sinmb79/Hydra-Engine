from hydra.exchange.base import BaseExchange
from hydra.logging.setup import get_logger

logger = get_logger(__name__)


class KISExchange(BaseExchange):
    """python-kis 래핑. 한국/미국 주식."""

    def __init__(self, app_key: str, app_secret: str, account_no: str, is_paper: bool = True):
        self._app_key = app_key
        self._app_secret = app_secret
        self._account_no = account_no
        self._is_paper = is_paper
        self._client = None

    def _get_client(self):
        if self._client is None:
            import pykis
            self._client = pykis.PyKis(
                id=self._app_key,
                account=self._account_no,
                appkey=self._app_key,
                appsecret=self._app_secret,
                virtual_account=self._is_paper,
            )
        return self._client

    async def get_balance(self) -> dict:
        client = self._get_client()
        account = client.account()
        return {"balance": float(account.balance)}

    async def create_order(self, symbol: str, side: str, order_type: str, qty: float, price: float | None = None) -> dict:
        client = self._get_client()
        stock = client.stock(symbol)
        if side == "buy":
            order = stock.buy(qty=int(qty), price=price)
        else:
            order = stock.sell(qty=int(qty), price=price)
        return {"order_id": str(order.number), "status": "submitted"}

    async def cancel_order(self, order_id: str) -> dict:
        client = self._get_client()
        client.cancel_order(order_id)
        return {"status": "canceled"}

    async def cancel_all(self) -> list:
        client = self._get_client()
        orders = client.pending_orders()
        canceled = []
        for o in orders:
            o.cancel()
            canceled.append(str(o.number))
        return canceled

    async def get_positions(self) -> list:
        client = self._get_client()
        account = client.account()
        return [
            {"symbol": s.symbol, "qty": s.qty, "avg_price": float(s.purchase_price), "side": "buy"}
            for s in account.stocks
        ]
