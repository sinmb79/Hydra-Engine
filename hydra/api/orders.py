from fastapi import APIRouter, Depends
from hydra.api.auth import verify_api_key
from hydra.core.order_queue import OrderRequest

router = APIRouter()
_order_queue = None


def set_order_queue(queue) -> None:
    global _order_queue
    _order_queue = queue


@router.post("/orders")
async def create_order(order: OrderRequest, _: str = Depends(verify_api_key)):
    return await _order_queue.submit(order)
