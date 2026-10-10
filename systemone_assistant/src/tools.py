"""Order tools backed by JSON files in systemone_assistant/data.

Every tool returns a dict with `ok: bool`. On success `data` holds the result; on failure
`error` holds a customer-safe reason. Write tools require the requesting customer's email to
match the order, and "not found" and "not yours" return the same error so order ids cannot be
probed.
"""
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ORDERS_PATH = DATA_DIR / "orders.json"
ESCALATIONS_PATH = DATA_DIR / "escalations.json"

# Orders can only be changed before the warehouse has picked them up.
MUTABLE_STATUSES = {"processing"}

DEPARTMENTS = ("billing", "technical", "sales", "other")

_NOT_FOUND = "I could not find that order on your account. Please check the order number."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def _write(path: Path, value: Any) -> None:
    # Write to a temp file in the same directory, then rename, so a crash never leaves a
    # half-written JSON file behind.
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _find_owned_order(order_id: str, customer_email: str) -> tuple[dict, dict | None]:
    """Return (all_orders, order); order is None when missing or owned by another customer."""
    orders = _read(ORDERS_PATH)
    order = orders.get(order_id)
    if order is None or order["customer_email"].lower() != customer_email.lower():
        return orders, None
    return orders, order


def get_order_status(order_id: str, customer_email: str) -> dict:
    _, order = _find_owned_order(order_id, customer_email)
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
    orders, order = _find_owned_order(order_id, customer_email)
    if order is None:
        return {"ok": False, "error": _NOT_FOUND}
    if order["status"] == "cancelled":
        return {"ok": False, "error": "This order is already cancelled."}
    if order["status"] not in MUTABLE_STATUSES:
        return {
            "ok": False,
            "error": f"This order is already '{order['status']}' and can no longer be cancelled. "
                     "You can request a return once it is delivered.",
        }
    order["status"] = "cancelled"
    order["cancelled_at"] = _now()
    order["cancel_reason"] = reason
    _write(ORDERS_PATH, orders)
    return {
        "ok": True,
        "data": {
            "order_id": order_id,
            "status": "cancelled",
            "refund_amount": order["total"],
            "currency": order["currency"],
        },
    }


def change_address(order_id: str, customer_email: str, new_address: str) -> dict:
    orders, order = _find_owned_order(order_id, customer_email)
    if order is None:
        return {"ok": False, "error": _NOT_FOUND}
    if order["status"] not in MUTABLE_STATUSES:
        return {
            "ok": False,
            "error": f"This order is already '{order['status']}', so the shipping address can no longer be changed.",
        }
    new_address = (new_address or "").strip()
    if not new_address:
        return {"ok": False, "error": "A new shipping address is required."}
    old_address = order["shipping_address"]
    order["shipping_address"] = new_address
    order["address_updated_at"] = _now()
    _write(ORDERS_PATH, orders)
    return {
        "ok": True,
        "data": {"order_id": order_id, "old_address": old_address, "new_address": new_address},
    }


def escalate_to_human(customer_email: str, department: str, summary: str) -> dict:
    if department not in DEPARTMENTS:
        return {"ok": False, "error": f"Unknown department {department!r}."}
    tickets = _read(ESCALATIONS_PATH)
    ticket = {
        "ticket_id": f"ESC-{len(tickets) + 1:05d}",
        "created_at": _now(),
        "customer_email": customer_email,
        "department": department,
        "summary": summary,
        "status": "open",
    }
    tickets.append(ticket)
    _write(ESCALATIONS_PATH, tickets)
    return {"ok": True, "data": {"ticket_id": ticket["ticket_id"], "department": department}}


# Action name -> backend tool. `chitchat` and `other` are deliberately absent: they need no
# backend call, the pipeline sends them straight to the LLM.
TOOLS: dict[str, Callable[..., dict]] = {
    "order_status": get_order_status,
    "cancel_order": cancel_order,
    "change_address": change_address,
    "escalate_to_human": escalate_to_human,
}
