from abc import ABC, abstractmethod


class BaseExchange(ABC):
    @abstractmethod
    async def get_balance(self) -> dict: ...

    @abstractmethod
    async def create_order(self, symbol: str, side: str, order_type: str, qty: float, price: float | None = None) -> dict: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> dict: ...

    @abstractmethod
    async def cancel_all(self) -> list: ...

    @abstractmethod
    async def get_positions(self) -> list: ...

    async def set_leverage(self, symbol: str, leverage: int) -> None:
        """레버리지 설정. 현물 거래소는 no-op (override 불필요)."""
        pass
