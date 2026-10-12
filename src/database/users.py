from pathlib import Path

from bson import ObjectId, json_util
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from ..config import mongodb_settings

ORDERS_FILE = Path(__file__).parent / "data" / "dummy_data.json"


class UserMongoDBHandler:
    """Handler class for MongoDB operations related to users."""

    def __init__(self):
        """Initialize MongoDB connection"""
        self.connection_string = mongodb_settings.uri
        self.database_name = mongodb_settings.database
        self.collection_name = "user_data"

        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def load_users(self) -> int:
        """Load dummy data into the collection, one document per user.

        Each user document holds only user data (userId, name, email, phone),
        without orders. Upserts by userId, so reloading the file does not
        create duplicates. Returns the number of users loaded.
        """
        user = json_util.loads(ORDERS_FILE.read_text())["user"]
        user_doc = {**user, "userId": ObjectId(user["userId"]["$ObjectId"])}
        self.collection.replace_one({"userId": user_doc["userId"]}, user_doc, upsert=True)
        return 1

    def close_connection(self):
        """Close the MongoDB connection"""
        self.client.close()
        print("MongoDB connection closed")    