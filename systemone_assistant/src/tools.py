"""Order tools backed by MongoDB (`orders` and `escalations` collections).

Every tool returns a dict with `ok: bool`. On success `data` holds the result; on failure
`error` holds a customer-safe reason. Write tools require the requesting customer's email to
match the order, and "not found" and "not yours" return the same error so order ids cannot be
probed.

Connection is read from the environment at call time:
  MONGO_URI   e.g. mongodb://user:pass@localhost:27017/?authSource=admin
  MONGO_DB    database name, default "systemone"
"""
import os
from datetime import datetime, timezone
from typing import Any, Callable

from pymongo import MongoClient, ReturnDocument
from pymongo.collation import Collation
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

# Orders can only be changed before the warehouse has picked them up.
MUTABLE_STATUSES = ["processing"]

DEPARTMENTS = ("billing", "technical", "sales", "other")

_NOT_FOUND = "I could not find that order on your account. Please check the order number."

# Email comparison is case-insensitive, matching the original behaviour.
_EMAIL_COLLATION = Collation(locale="en", strength=2)

_client: MongoClient | None = None


def _db():
    global _client
    if _client is None:
        _client = MongoClient(os.environ.get("MONGO_URI", "mongodb://localhost:27017"))
    return _client[os.environ.get("MONGO_DB", "systemone")]


def _orders() -> Collection:
    return _db()["orders"]


def _escalations() -> Collection:
    return _db()["escalations"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _owned(order_id: str, customer_email: str) -> dict[str, Any]:
    """Filter that matches the order only if it belongs to this customer."""
    return {"_id": order_id, "customer_email": customer_email}


def _find_owned_order(order_id: str, customer_email: str) -> dict | None:
    return _orders().find_one(_owned(order_id, customer_email), collation=_EMAIL_COLLATION)


def get_order_status(order_id: str, customer_email: str) -> dict:
    order = _find_owned_order(order_id, customer_email)
    if order is None:
        return {"ok": False, "error": _NOT_FOUND}
    data = {
        "order_id": order_id,
        "status": order["status"],
        "placed_at": order["placed_at"],
        "estimated_delivery": order.get("estimated_delivery"),
        "delivered_at": order.get("delivered_at"),
        "carrier": order.get("carrier"),
        "tracking_number": order.get("tracking_number"),
        "total": order["total"],
        "currency": order["currency"],
    }
    return {"ok": True, "data": data}


def cancel_order(order_id: str, customer_email: str, reason: str | None = None) -> dict:
    # Check-and-set in one update: the status guard is part of the filter, so two concurrent
    # cancels cannot both succeed.
    updated = _orders().find_one_and_update(
        {**_owned(order_id, customer_email), "status": {"$in": MUTABLE_STATUSES}},
        {"$set": {"status": "cancelled", "cancelled_at": _now(), "cancel_reason": reason}},
        collation=_EMAIL_COLLATION,
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        order = _find_owned_order(order_id, customer_email)
        if order is None:
            return {"ok": False, "error": _NOT_FOUND}
        if order["status"] == "cancelled":
            return {"ok": False, "error": "This order is already cancelled."}
        return {
            "ok": False,
            "error": f"This order is already '{order['status']}' and can no longer be cancelled. "
                     "You can request a return once it is delivered.",
        }
    return {
        "ok": True,
        "data": {
            "order_id": order_id,
            "status": "cancelled",
            "refund_amount": updated["total"],
            "currency": updated["currency"],
        },
    }


def change_address(order_id: str, customer_email: str, new_address: str) -> dict:
    new_address = (new_address or "").strip()
    if not new_address:
        return {"ok": False, "error": "A new shipping address is required."}
    # Same check-and-set as cancel: the status guard lives in the filter.
    before = _orders().find_one_and_update(
        {**_owned(order_id, customer_email), "status": {"$in": MUTABLE_STATUSES}},
        {"$set": {"shipping_address": new_address, "address_updated_at": _now()}},
        collation=_EMAIL_COLLATION,
        return_document=ReturnDocument.BEFORE,
    )
    if before is None:
        order = _find_owned_order(order_id, customer_email)
        if order is None:
            return {"ok": False, "error": _NOT_FOUND}
        return {
            "ok": False,
            "error": f"This order is already '{order['status']}', so the shipping address can no longer be changed.",
        }
    return {
        "ok": True,
        "data": {"order_id": order_id, "old_address": before["shipping_address"], "new_address": new_address},
    }


def escalate_to_human(customer_email: str, department: str, summary: str) -> dict:
    if department not in DEPARTMENTS:
        return {"ok": False, "error": f"Unknown department {department!r}."}
    escalations = _escalations()
    # Next id is one past the highest existing ticket. Two concurrent escalations can compute the
    # same id; the unique index rejects the loser, so re-read and retry.
    for _ in range(5):
        last = escalations.find_one(sort=[("ticket_id", -1)])
        next_number = int(last["ticket_id"].split("-")[1]) + 1 if last else 1
        ticket = {
            "ticket_id": f"ESC-{next_number:05d}",
            "created_at": _now(),
            "customer_email": customer_email,
            "department": department,
            "summary": summary,
            "status": "open",
        }
        try:
            escalations.insert_one(ticket)
        except DuplicateKeyError:
            continue
        return {"ok": True, "data": {"ticket_id": ticket["ticket_id"], "department": department}}
    return {"ok": False, "error": "Could not create a support ticket right now. Please try again."}


# Action name -> backend tool. `chitchat` and `other` are deliberately absent: they need no
# backend call, the pipeline sends them straight to the LLM.
TOOLS: dict[str, Callable[..., dict]] = {
    "order_status": get_order_status,
    "cancel_order": cancel_order,
    "change_address": change_address,
    "escalate_to_human": escalate_to_human,
}
