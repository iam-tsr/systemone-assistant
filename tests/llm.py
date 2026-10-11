from dotenv import load_dotenv

from src.config import client

load_dotenv()

def test_llm_invoke():
    llm = client()
    print(llm.invoke("Hello"))

if __name__ == "__main__":
    test_llm_invoke()