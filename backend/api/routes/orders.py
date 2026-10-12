from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from ...database import OrderRepository, UserRepository
from ..deps import get_db
from ..schemas import OrderResponse, OrdersResponse

router = APIRouter()


def _current_user_id(db: Database) -> str:
    user = UserRepository(db).current_user()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user["userId"]


@router.get("/orders", response_model=OrdersResponse)
def list_orders(db: Database = Depends(get_db)) -> OrdersResponse:
    user_id = _current_user_id(db)
    return OrdersResponse(orders=OrderRepository(db).list_for_user(user_id))


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Database = Depends(get_db)) -> OrderResponse:
    user_id = _current_user_id(db)
    order = OrderRepository(db).get_for_user(user_id, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderResponse(order=order)
