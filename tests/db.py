from src.database.orders import OrderMongoDBHandler

order_handler = OrderMongoDBHandler()

def check_orders():
    """Run each order method against MongoDB and print the output."""
    try:
        print("load_orders:", order_handler.load_orders())

        print("order_status ORD-2026-00001:", order_handler.order_status("ORD-2026-00001"))
        print("order_status ORD-X:", order_handler.order_status("ORD-X"))

        new_address = {
            "street": "1 Test St",
            "city": "Mumbai",
            "state": "Maharashtra",
            "postalCode": "400001",
            "country": "IN",
        }
        print("update_address ORD-2026-00002:", order_handler.update_address("ORD-2026-00002", new_address))
        print("  stored:", order_handler.collection.find_one({"orderId": "ORD-2026-00002"}, {"_id": 0, "shippingAddress": 1}))

        print("cancel_order ORD-2026-00003:", order_handler.cancel_order("ORD-2026-00003"))
        print("  stored:", order_handler.collection.find_one(
            {"orderId": "ORD-2026-00003"},
            {"_id": 0, "status": 1, "expectedDeliveryDate": 1, "deliveryDate": 1},
        ))
        print("cancel_order ORD-X:", order_handler.cancel_order("ORD-X"))

        print("restore:", order_handler.load_orders())
    finally:
        order_handler.close_connection()

def load_order_data():
    """Load dummy data into the collection."""
    try:
        print("load_orders:", order_handler.load_orders())
    finally:
        order_handler.close_connection()


if __name__ == "__main__":
    # check_orders()
    load_order_data()
