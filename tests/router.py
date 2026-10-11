from src.tool_route import route

def test_route() -> None:
    state1 = [
        {"HumanMessage": "Hi", "AI_MESSAGE": "Hello! How can I assist you today?", "AIMessage": "Hello! How can I assist you today?"},
        {"HumanMessage": "I want to cancel my order and get a refund.", "AI_MESSAGE": "I'm sorry to hear that. I can help you with that. Can you please provide your order number?", "AIMessage": "I'm sorry to hear that. I can help you with that. Can you please provide your order number?"},
        {"HumanMessage": "Okay", "AI_MESSAGE": "Great! I'll process that for you right away.", "AIMessage": "Great! I'll process that for you right away."},
        {"HumanMessage": "Thanks, I also want to change my shipping address."}
    ]
    state2 = [{"HumanMessage": "Hi"}]
    state3 = [{"HumanMessage": "I ordered a product but it hasn't arrived yet. Can you tell me when it will be delivered?"}]
    return route(state3)

if __name__ == "__main__":
    test_route()