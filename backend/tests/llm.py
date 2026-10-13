from src.config import client

def test_llm_invoke():
    llm = client()
    
    response = llm.invoke("Hello")
    return response.text

if __name__ == "__main__":
    print(test_llm_invoke())