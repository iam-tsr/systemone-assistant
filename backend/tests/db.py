from src.database import OrderMongoDBHandler


def check_orders():
    """Run each order method against MongoDB and print the output."""
    try:
        order_handler = OrderMongoDBHandler()

        print("order_status 10003:", order_handler.order_status("10003"))

        new_address = "1 Test St, Mumbai, Maharashtra 400001"
        print("update_address 10002:", order_handler.update_address("10002", new_address))

        print("cancel_order 10001:", order_handler.cancel_order("10001"))
    finally:
        order_handler.close_connection()

def load_order_data():
    """Load dummy data into the collection."""
    try:
        order_handler = OrderMongoDBHandler()
        print("load_orders:", order_handler.load_orders())
    finally:
        order_handler.close_connection()


if __name__ == "__main__":
    # check_orders()
    load_order_data()
