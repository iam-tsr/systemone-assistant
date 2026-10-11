from systemone_assistant.src.config import chat, slm_endpoint

def test_slm_endpoint() -> str:
    return chat(
        slm_endpoint(),
        messages=[{"role": "user", "content": "Hello, you are so awesome!"}],
        temperature=0.0,
    )

if __name__ == "__main__":
    result = test_slm_endpoint()
    print(result)