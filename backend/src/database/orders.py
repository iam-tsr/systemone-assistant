from pathlib import Path

from bson import ObjectId, json_util
from pymongo import MongoClient, ReplaceOne
from pymongo.errors import ConnectionFailure

from ..config import mongodb_settings

ORDERS_FILE = Path(__file__).parent / "data" / "dummy_data.json"


class OrderMongoDBHandler:
    """Handler class for MongoDB operations related to orders."""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.connection_string = mongodb_settings.uri
        self.database_name = mongodb_settings.database
        self.collection_name = "order_data"

        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def load_orders(self) -> int:
        """Load dummy data into the collection, one document per order.

        Each order document carries only the userId of the user block from the
        file, not the full user. Upserts by orderId, so reloading the file does
        not create duplicates. Returns the number of orders loaded.
        """
        try:
            data = json_util.loads(ORDERS_FILE.read_text())
            user_id = ObjectId(data["user"]["userId"]["$ObjectId"])
            operations = [
                ReplaceOne({"orderId": order["orderId"]}, {"orderId": order["orderId"], "userId": user_id, **{k: v for k, v in order.items() if k != "orderId"}}, upsert=True)
                for order in data["orders"]
            ]
            if operations:
                self.collection.bulk_write(operations)
            return len(operations)
        except Exception as e:
            print(f"Error loading orders: {e}")
            return 0

    def order_status(self, order_id: str) -> dict | None:
        """Return the status, items, and delivery date (if set) of an order.

        Returns None when no order has the given orderId.
        """
        try:
            check_order_status = self.collection.find_one({"orderId": order_id},{"status": 1})
            if check_order_status["status"] == "cancelled":
                return self.collection.find_one({"orderId": order_id},{"status": 1, "items": 1, "totalAmount": 1})
            elif check_order_status["status"] == "delivered":
                return self.collection.find_one({"orderId": order_id},{"status": 1, "items": 1, "totalAmount": 1, "deliveryDate": 1})
            elif check_order_status["status"] == "processing":
                return self.collection.find_one({"orderId": order_id},{"status": 1, "items": 1, "totalAmount": 1, "expectedDeliveryDate": 1})
            elif check_order_status["status"] == "shipped":
                return self.collection.find_one({"orderId": order_id},{"status": 1, "items": 1, "totalAmount": 1, "expectedDeliveryDate": 1, "shippingDate": 1})
            else:
                return None
        except Exception as e:
            print(f"Error fetching order status: {e}")
            return None

    def update_address(self, order_id: str, shipping_address: str) -> bool:
        """Replace the shipping address of an order.

        Only orders still in 'processing' can have their address changed. Orders in any
        other status are left untouched.

        Returns True if the address of an order was updated.
        """
        try:
            result = self.collection.update_one(
                {"orderId": order_id, "status": "processing"},
                {"$set": {"shippingAddress": shipping_address}},
            )
            return result.matched_count == 1
        except Exception as e:
            print(f"Error updating shipping address: {e}")
            return False

    CANCELLABLE_STATUSES = ("processing", "shipped")

    def cancel_order(self, order_id: str) -> bool:
        """Mark an order as cancelled and remove its expected and delivery dates.

        Only orders still in a cancellable status are updated. Delivered or already
        cancelled orders are left untouched.

        Returns True if an order with the given orderId was cancelled.
        """
        result = self.collection.update_one(
            {"orderId": order_id, "status": {"$in": list(self.CANCELLABLE_STATUSES)}},
            {
                "$set": {"status": "cancelled"},
                "$unset": {"expectedDeliveryDate": "", "deliveryDate": ""},
            },
        )
        return result.modified_count == 1


    def close_connection(self):
        """Close the MongoDB connection"""
        try:
            self.client.close()
            return True
        except Exception as e:
            print(f"Error closing MongoDB connection: {e}")
            return False