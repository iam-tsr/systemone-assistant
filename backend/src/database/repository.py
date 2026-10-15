from datetime import datetime
from typing import Any

from bson import ObjectId

from .users import  UserMongoDBHandler
from .orders import OrderMongoDBHandler

# Excluded from API responses. Mongo's _id is not part of the public contract.
_HIDE_ID = {"_id": 0}


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _order_out(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "orderId": doc["orderId"],
        "orderDate": _iso(doc.get("orderDate")),
        "status": doc["status"],
        "items": doc.get("items", []),
        "shippingAddress": doc.get("shippingAddress", ""),
        "paymentMethod": doc.get("paymentMethod", ""),
        "totalAmount": doc.get("totalAmount", 0),
        "expectedDeliveryDate": _iso(doc.get("expectedDeliveryDate")),
        "deliveryDate": _iso(doc.get("deliveryDate")),
    }


class UserRepository(UserMongoDBHandler):
    """Read access to user_data. Takes an injected Database so the API shares one client."""

    def current_user(self) -> dict[str, Any] | None:
        """Return the profile of the current user.

        No auth exists yet, so this is the first user document. Replace with a
        session lookup once login is added.
        """
        doc = self.collection.find_one({}, _HIDE_ID, sort=[("_id", 1)])
        if doc is None:
            return None
        return {
            "userId": str(doc["userId"]),
            "name": doc["name"],
            "email": doc["email"],
            "phone": doc["phone"],
        }


class OrderRepository(OrderMongoDBHandler):
    """Read access to order_data, scoped to a user."""

    def list_for_user(self, user_id: str) -> list[dict[str, Any]]:
        cursor = self.collection.find(
            {"userId": ObjectId(user_id)}, _HIDE_ID
        ).sort("orderDate", -1)
        return [_order_out(doc) for doc in cursor]

    def get_for_user(self, user_id: str, order_id: int) -> dict[str, Any] | None:
        doc = self.collection.find_one(
            {"userId": ObjectId(user_id), "orderId": order_id}, _HIDE_ID
        )
        return _order_out(doc) if doc is not None else None
