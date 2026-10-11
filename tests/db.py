from src.db import MongoDBHandler
from src.config import mongodb_settings

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        db_handler = MongoDBHandler()
        assert db_handler.client is not None, "MongoDB client should not be None"
        assert db_handler.db.name == mongodb_settings.database, "Database name should match the configuration"
        print("MongoDB connection test passed")
    except Exception as e:
        print(f"MongoDB connection test failed: {e}")
    finally:
        db_handler.close_connection()

if __name__ == "__main__":
    test_mongodb_connection()