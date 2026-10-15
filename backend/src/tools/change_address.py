

from langchain.tools import tool
from ..database import OrderMongoDBHandler

@tool
async def change_address(orderid: int, new_address: str) -> str:
    """Change the address for an order and return a confirmation message.
    
    Args:
        orderid (int): The ID of the order to change the address for.
        new_address (str): The new address to set for the order.
        
    Returns:
        str: A confirmation message.
    """

    order_handler = None
    try:
        order_handler = OrderMongoDBHandler()

        current = order_handler.order_status(orderid)
        if current is None:
            return f"Order {orderid} could not be found."
        elif current['status'] == 'processing':
            result = order_handler.update_address(orderid, new_address)
            if result:
                return f"Address for order {orderid} has been updated to: {new_address}"
        return (
            f"Order {orderid}'s address cannot be changed because its status is "
            f"'{current['status']}'. Addresses can only be changed while the order is processing."
        )

    except Exception as e:
        return f"An error occurred while trying to change the address: {str(e)}"
    finally:
        if order_handler is not None:
            order_handler.close_connection()