

from langchain.tools import tool
from ..database import OrderMongoDBHandler

@tool
async def cancel_order(orderid: str) -> str:
    """Cancel an order and return a confirmation message.
    
    Args:
        orderid (str): The ID of the order to cancel.

    Returns:
        str: A confirmation message.
    """

    try:
        # Create an instance of the OrderMongoDBHandler
        order_handler = OrderMongoDBHandler()

        # Cancel the order using the provided order ID
        result = order_handler.cancel_order(orderid)

        if result:
            return f"Order {orderid} has been successfully canceled."
        else:
            return f"Order {orderid} could not be found or canceled."
        
    except Exception as e:
        return f"An error occurred while trying to cancel the order: {str(e)}"
    finally:
        order_handler.close_connection()