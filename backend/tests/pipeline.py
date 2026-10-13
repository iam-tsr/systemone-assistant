from src.pipeline import handle_message

if __name__ == "__main__":
# Run until the user types "exit"
    while True:
        user_input = input("User: ")
        if user_input.lower() == "exit":
            break
        response = handle_message("1234", user_input)
        print(f"Assistant: {response['reply']} (action: {response['action']})")