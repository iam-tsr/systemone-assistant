from src.database import UserMongoDBHandler, OrderMongoDBHandler

if __name__ == "__main__":
    # Load dummy data into MongoDB
    user_handler = UserMongoDBHandler()
    num_users_loaded = user_handler.load_users()
    print(f"Loaded {num_users_loaded} user(s) into MongoDB.")
    user_handler.close_connection()

    order_handler = OrderMongoDBHandler()
    num_orders_loaded = order_handler.load_orders()
    print(f"Loaded {num_orders_loaded} order(s) into MongoDB.")
    order_handler.close_connection()