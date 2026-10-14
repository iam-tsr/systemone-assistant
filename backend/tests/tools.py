from src.tools import order_status

async def test_order_status():
    # Test with a valid order ID
    valid_order_id = "10001"
    result = await order_status(valid_order_id)
    print(f"Test with valid order ID {valid_order_id}: {result}")

    # Test with an invalid order ID
    invalid_order_id = "99999"
    result = await order_status(invalid_order_id)
    print(f"Test with invalid order ID {invalid_order_id}: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_order_status())