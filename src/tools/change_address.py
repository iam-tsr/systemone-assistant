

from langchain.tools import tool
from ..database import OrderMongoDBHandler

@tool
async def change_address(orderid: str, new_address: str) -> str:
    """Change the address for an order and return a confirmation message.
    
    Args:
        orderid (str): The ID of the order to change the address for.
        new_address (str): The new address to set for the order.
        
    Returns:
        str: A confirmation message.
    """

    order_handler = None
    try:
        order_handler = OrderMongoDBHandler()
        result = order_handler.update_address(orderid, new_address)
        if result:
            return f"Address for order {orderid} has been updated to: {new_address}"
        else:
            return f"Failed to update address for order {orderid}. Please check the order ID and try again."

    except Exception as e:
        return f"An error occurred while trying to change the address: {str(e)}"
    finally:
        if order_handler is not None:
            order_handler.close_connection()