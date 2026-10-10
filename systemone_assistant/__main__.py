from .src import handle_message

def main() -> None:
    """Run the assistant in a simple command-line loop."""
    print("Welcome to the SystemOne Assistant!")
    print("Type 'exit' to quit.")
    customer_email = input("Enter your email: ").strip()
    while True:
        message = input("You: ").strip()
        if message.lower() == "exit":
            break
        response = handle_message(message, customer_email)
        print(f"Assistant: {response['reply']}")

if __name__ == "__main__":
    main()