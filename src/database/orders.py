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
        data = json_util.loads(ORDERS_FILE.read_text())
        user_id = ObjectId(data["user"]["userId"]["$ObjectId"])
        operations = [
            ReplaceOne({"orderId": order["orderId"]}, {"orderId": order["orderId"], "userId": user_id, **{k: v for k, v in order.items() if k != "orderId"}}, upsert=True)
            for order in data["orders"]
        ]
        if operations:
            self.collection.bulk_write(operations)
        return len(operations)

    def close_connection(self):
        """Close the MongoDB connection"""
        self.client.close()
        print("MongoDB connection closed")
    