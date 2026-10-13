


from langchain.tools import tool
from ..database import OrderMongoDBHandler

@tool
async def order_status(orderid: str) -> str:
    """Check the status of an order and return the status information.
    
    Args:
        orderid (str): The ID of the order to check the status for.
        
    Returns:
        str: A message indicating the status of the order.
    """

    order_handler = None
    try:
        # Create an instance of the OrderMongoDBHandler
        order_handler = OrderMongoDBHandler()

        # Retrieve the order status using the provided order ID
        status = order_handler.order_status(orderid)

        if status:
            return f"The status of order {orderid} is: {status}"
        else:
            return f"Order {orderid} could not be found."

    except Exception as e:
        return f"An error occurred while trying to check the order status: {str(e)}"
    finally:
        # Ensure the database connection is closed
        if order_handler is not None:
            order_handler.close_connection()