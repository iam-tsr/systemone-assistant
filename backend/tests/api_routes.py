from src.api.routes.orders import list_orders, get_order
from src.api.routes.profile import get_profile

def test_list_orders():
    return list_orders()

def test_get_order():
    order_id = "10001"
    return get_order(order_id)

def test_get_profile():
    return get_profile()

if __name__ == "__main__":
    print(test_list_orders())
    print(test_get_order())
    print(test_get_profile())