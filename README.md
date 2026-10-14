# SystemOne Assistant

SystemOne Assistant is a voice-first customer support application for an online
store. Users speak into the web interface, the backend transcribes the audio,
routes the request, performs order operations when needed, generates a response,
and returns synthesized WAV audio for browser playback.

## Architecture



## Project structure

```text
backend/
  main.py                 FastAPI/Uvicorn entry point
  src/api/                API factory, dependencies, and routes
  src/pipeline.py         Guardrails, routing, tools, and response flow
  src/database/           MongoDB repositories and seed data
  src/memory.py           LangGraph conversation checkpointing
  src/voice/              Gnani STT/TTS wrappers
  tests/                  Backend test and smoke-test scripts

frontend/
  src/App.tsx             Main React application
  src/components/         Voice UI, profile UI, and shared components
  src/lib/voice.ts        Recording, WAV conversion, API calls, and playback
  vite.config.ts          Vite server and backend proxy configuration

docker-compose.yml        MongoDB, backend, and frontend services
```

## Requirements

- A running SystemOne/JEV model server
- An OpenAI-compatible model server
- Gnani API credentials
- Docker Engine and Docker Compose.

## Configuration

Copy the environment templates and fill in real credentials:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

## Run with Docker Compose

Compose uses values from `backend/.env` for MongoDB initialization and
environment substitution. Start the full stack from the repository root:

```bash
docker compose --build
```

Run detached:

```bash
docker compose --build -d
```

## API overview

All application routes are prefixed with `/api`.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Backend health check |
| `GET` | `/api/profile` | Current user profile |
| `GET` | `/api/orders` | Current user's orders |
| `GET` | `/api/orders/{order_id}` | One order |
| `POST` | `/api/voice/agent/{session_id}` | Audio turn through STT, pipeline, and TTS |

The voice endpoint expects a multipart upload with a `file` field. The frontend
generates a UUID per voice session and reuses it across turns so conversation
history is preserved.

## License

MIT