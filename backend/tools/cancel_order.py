

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

    order_handler = None
    try:
        # Create an instance of the OrderMongoDBHandler
        order_handler = OrderMongoDBHandler()

        # Cancel the order using the provided order ID
        result = order_handler.cancel_order(orderid)

        if result:
            return f"Order {orderid} has been successfully canceled."

        current = order_handler.order_status(orderid)
        if current is None:
            return f"Order {orderid} could not be found."
        return (
            f"Order {orderid} cannot be cancelled because its status is "
            f"'{current['status']}'. Only orders that are processing or shipped can be cancelled."
        )
        
    except Exception as e:
        return f"An error occurred while trying to cancel the order: {str(e)}"
    finally:
        if order_handler is not None:
            order_handler.close_connection()