from fastapi import APIRouter, HTTPException

from ...database import OrderRepository, UserRepository
from ..schemas import OrderResponse, OrdersResponse

router = APIRouter()


def _current_user_id() -> str:
    user = UserRepository().current_user()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user["userId"]


@router.get("/orders", response_model=OrdersResponse)
def list_orders() -> OrdersResponse:
    user_id = _current_user_id()
    return OrdersResponse(orders=OrderRepository().list_for_user(user_id))


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int) -> OrderResponse:
    user_id = _current_user_id()
    order = OrderRepository().get_for_user(user_id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(order=order)
