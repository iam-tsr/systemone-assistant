from langchain_openai import ChatOpenAI

def client(
        model: str = "gpt-4o-mini", 
        base_url: str = "http://localhost:8080/v1",
        max_tokens: int = 512, 
        temperature: float = 0.0,
    ) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        base_url=base_url,
        max_completion_tokens=max_tokens,
        temperature=temperature,
    )