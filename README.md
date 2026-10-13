## Services

Laya model server:

```
llama-server -hf ggml-org/Laya-GGUF -ngl 999 --embeddings --pooling none -c 2048 -ub 2048 -b 2048 --port 8000
```

feder-cr/jev -> ./jev serve --port 8000

MongoDB (orders, escalations, and conversation checkpoints). Seeded from `systemone_assistant/data/` on first start of an empty volume:

```
cp mongo/.env.example mongo/.env   # set MONGO_ROOT_PASSWORD
docker build -f mongo/Dockerfile -t systemone-mongo:7 .
docker run -d --name systemone-mongo -p 27017:27017 \
  --env-file mongo/.env \
  -e MONGO_INITDB_ROOT_USERNAME=$MONGO_ROOT_USER -e MONGO_INITDB_ROOT_PASSWORD=$MONGO_ROOT_PASSWORD \
  -e MONGO_INITDB_DATABASE=systemone \
  -v systemone-mongo-data:/data/db systemone-mongo:latest
```

The app reads:

```
MONGO_URI=mongodb://root:<password>@localhost:27017/?authSource=admin
MONGO_DB=systemone
```

## Voice request flow

The voice UI uses one request per turn:

1. The browser opens the microphone after the user presses **Speak**.
2. A `MediaRecorder` captures the utterance and stops automatically after 900 ms of
   silence (or 15 seconds).
3. The browser decodes the recording and encodes it as PCM WAV, which is the format
   accepted by the Gnani STT API.
4. `POST /api/voice/agent/{session_id}` performs STT, runs the SystemOne pipeline, and performs
   TTS. It returns the reply as `audio/wav`; the transcript is provided in the
   `X-Transcript` response header. The Vite frontend generates one UUID per voice
   session and sends it as `session_id` so conversation history is preserved
   across turns.
5. The browser plays the returned WAV and returns to the idle state.

`POST /api/voice/stt` and `POST /api/voice/tts` remain available for clients that
need the individual stages. The Vite development proxy in
`frontend/vite.config.ts` forwards `/api/*` requests to the FastAPI service.

Seeding only runs when the volume is empty. Remove the volume (`docker volume rm systemone-mongo-data`) to reseed; this discards all orders, tickets, and conversation history.
