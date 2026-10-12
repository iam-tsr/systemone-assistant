from backend.memory import chat, get_chat_history, clear_chat_history

if __name__ == "__main__":
    thread_id = 1
    
    # Invoke the chat function
    response = chat(thread_id, "My name is Tushar")
    reponse = chat(thread_id, "What is my name?")
    
    # Retrieve chat history
    history = get_chat_history(thread_id)
    print("Chat History:", history)
    
    # Clear chat history
    clear_chat_history(thread_id)
    print("Chat history cleared.")