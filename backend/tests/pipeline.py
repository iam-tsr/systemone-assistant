from src.pipeline import handle_message
from src.memory import clear_chat_history

if __name__ == "__main__":
    thread_id = "1234"
    
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            clear_chat_history(thread_id)
            break
        response = handle_message(thread_id, user_input)
        print(f"Assistant: {response['reply']} (action: {response['action']})")