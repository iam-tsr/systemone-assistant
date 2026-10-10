from systemone_assistant.src.guardrails import guardrail

def main() -> None:
    state = "I want to cancel my order and get a refund."
    
    guardrail_results = guardrail(state)
    print(guardrail_results)

if __name__ == "__main__":
    main()