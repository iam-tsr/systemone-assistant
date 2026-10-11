from src.config import client

def test_llm_invoke():
    llm = client()
    response = llm.invoke("Hello")
    return response

if __name__ == "__main__":
    test_llm_invoke()