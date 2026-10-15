from typing import Any

from pydantic import BaseModel


class Profile(BaseModel):
    userId: str
    name: str
    email: str
    phone: str


class ProfileResponse(BaseModel):
    user: Profile


class Order(BaseModel):
    orderId: int
    orderDate: str | None
    status: str
    items: list[dict[str, Any]]
    shippingAddress: str
    paymentMethod: str
    totalAmount: float
    expectedDeliveryDate: str | None
    deliveryDate: str | None


class OrdersResponse(BaseModel):
    orders: list[Order]


class OrderResponse(BaseModel):
    order: Order

