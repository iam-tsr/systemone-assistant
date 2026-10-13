from src.api import create_app
from src.config import unicorn_settings

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=unicorn_settings.host,
        port=unicorn_settings.port,
        reload=True
    )