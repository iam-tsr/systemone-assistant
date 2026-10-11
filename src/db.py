from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from .config import mongodb_settings

class MongoDBHandler:
    """Handler class for MongoDB operations"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        # Get configuration from environment variables if not provided
        self.connection_string = mongodb_settings.uri
        self.database_name = mongodb_settings.database
        
        try:
            self.client = MongoClient(self.connection_string)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def close_connection(self):
        """Close the MongoDB connection"""
        self.client.close()
        print("MongoDB connection closed")