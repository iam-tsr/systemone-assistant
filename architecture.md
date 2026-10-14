# SystemOne Assistant — Architecture Diagram

**SystemOne Assistant** is a voice-first customer support application for an online store.
Users speak into a web interface, the backend transcribes audio, routes the request,
performs order operations, generates a response, and returns synthesized WAV audio
for browser playback.

---

## 1. High-Level Architecture

```mermaid
flowchart LR
    subgraph Client["Browser / User"]
        User["User (Voice Input)"]
    end

    subgraph Frontend["Vite Frontend (Next.js)"]
        App["Voice UI"]
        VoiceLib["Playback"]
        VoicePersona["Voice Status Animation"]
    end

    subgraph Network["Docker Network Proxy"]
        Proxy["Vite Dev/Preview Proxy<br/>(/api/* → backend)"]
    end

    subgraph Backend["FastAPI Backend"]
        AppFactory["App Factory, Lifespan, CORS, Routes"]
        Pipeline["Guardrails, Routing, Tools, Response Flow"]
        Memory["LangGraph Conversation Checkpointing"]
        Voice["Gnani STT/TTS Wrappers"]
        Tools["Order Tools + Intent Routing"]
        Guardrails["Safety / Churn Risk Assessment"]
        Config["Settings, LLM, Prompts"]
    end

    subgraph Storage["Data Layer"]
        MongoDB["MongoDB 7<br/>(orders_data, user_data, LangGraph checkpoints)"]
        SystemOne["SystemOne / Laya Model Server<br/>(STT, TTS, Routing, Entity Recognition)"]
        OpenAI["OpenAI-Compatible Model Server<br/>(Customer Reply Generation)"]
    end

    User -->|"POST<br/>Multipart audio upload"| App
    App --> VoiceLib
    App --> VoicePersona
    VoiceLib -->|"POST"| Proxy
    Proxy --> AppFactory
    AppFactory --> Pipeline
    AppFactory --> Memory
    AppFactory --> Voice
    AppFactory --> Tools
    AppFactory --> Guardrails
    AppFactory --> Config

    Pipeline -->|"Guardrail Risk Check"| Guardrails
    Pipeline -->|"Fetch Conversation History"| Memory
    Pipeline -->|"Route Intent"| Tools
    Pipeline -->|"Run Order Tool / Invoke Tool"| Tools
    Pipeline -->|"Generate Reply (LLM)"| OpenAI
    Pipeline -->|"Persist Checkpoints"| Memory
    Pipeline -->|"STT Transcribe"| Voice
    Pipeline -->|"TTS Synthesize"| Voice

    Memory -->|"Read / Write Checkpoints"| MongoDB
    Voice -->|"STT / TTS"| SystemOne
    Tools -->|"Order Operations"| MongoDB
    Tools -->|"Intent Routing"| SystemOne
    Tools -->|"Entity Recognition"| SystemOne
```

---

## 2. Data Flow Diagram

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend (Voice)
    participant B as Backend (FastAPI)
    participant P as Pipeline
    participant G as Guardrails
    participant M as Memory (LangGraph)
    participant S as SystemOne/Laya
    participant O as OpenAI Model
    participant D as MongoDB
    participant V as Gnani STT/TTS

    U->>F: Speak into web interface
    F->>F: Generate WAV buffer + UUID session_id
    F->>B: POST /api/voice/agent/{session_id} (audio)

    B->>V: STT Transcribe (audio → text)
    V-->>B: Transcript text

    B->>G: Guardrail Check (risk / churn)
    alt Risk score = 1 (blocked)
        G-->>B: Blocked signal
        B-->>F: Reply + action=blocked (no memory write)
        F-->>U: Play blocked reply audio
    else Churn risk > 0.85
        G-->>B: Escalation signal
        B->>O: Generate escalation reply
        B-->>F: Reply + action=escalate_to_human
        F-->>U: Play reply audio
    else Normal
        B->>M: Fetch chat history (thread_id)
        M-->>B: Conversation messages
        B->>M: Append HumanMessage (current)
        M-->>B: Updated conversation

        B->>S: Route Intent (systemone/slm)
        S-->>B: Action + confidence

        B->>O: Generate reply (with tool result / history)
        O-->>B: Reply text

        B->>M: Persist checkpoints (reply)
        M-->>B: Checkpoint committed

        B->>V: TTS Synthesize (reply → WAV)
        V-->>B: WAV bytes

        B-->>F: WAV audio + headers (transcript/reply/action)
        F-->>U: Play reply audio
    end
```

---

## 3. Component Responsibility Diagram

```mermaid
flowchart TB
    subgraph Backend["Backend (FastAPI)"]
        direction TB
        API["api/
            - app.py: App Factory, Lifespan, CORS, Router Mount"]
        ROUTES["api/routes/
            - voice.py: Voice Agent Endpoint"]
        SCHEMAS["api/schemas.py: Pydantic Models"]
        DEP["api/deps.py: Dependencies"]

        PIPE["pipeline.py:<br/>handle_message, _route, _run_operation"]
        MEM["memory.py:<br/>chat, get_chat_history, clear_chat_history"]
        GUARD["guardrails.py:<br/>risk_score, churn_risk"]
        TOOL["tool_route.py:<br/>systemone_route, slm_route"]
        ENTITY["entity_recognition.py:<br/>extract_entity"]
        TOOLS["tools/ + src/tools/:<br/>order_status, cancel_order,<br/>change_address, escalate_to_human"]
        VOICE["voice/ + src/voice/:<br/>stt.py (Gnani STT), tts.py (Gnani TTS)"]
        CONFIG["config/ + src/config/:<br/>settings, llm, systemone"]
        PROMPT["prompt.py:<br/>GEN_SYSTEM_PROMPT"]
    end

    subgraph Frontend["Frontend (Vite/Next.js)"]
        direction TB
        APP["App.tsx:<br/>Layout, Conversation UI, Voice UI"]
        VOICE_C["components/voice-persona.tsx:<br/>Voice Status / Persona Animation"]
        VOICE_LIB["lib/voice.ts:<br/>Recording, WAV, API, Playback"]
        TYPES["lib/types.ts:<br/>Profile, Order Types"]
    end

    subgraph External["External Services"]
        LAYA["SystemOne / Laya<br/>(STT, TTS, Routing, Entity)"]
        OPENAI["OpenAI-Compatible<br/>(Reply Generation)"]
        MONGO["MongoDB 7<br/>(orders, users, checkpoints)"]
    end

    API --> ROUTES
    ROUTES --> SCHEMAS
    ROUTES --> PIPE
    ROUTES --> VOICE
    PIPE --> MEM
    PIPE --> GUARD
    PIPE --> TOOL
    PIPE --> ENTITY
    PIPE --> TOOLS
    PIPE --> OPENAI
    MEM --> MONGO
    TOOLS --> MONGO
    TOOLS --> LAYA
    ENTITY --> LAYA
    VOICE --> LAYA
    CONFIG --> PROMPT
    CONFIG --> LAYA
    APP --> VOICE_LIB
    APP --> VOICE_C
    VOICE_LIB --> TYPES
    APP -->|"POST /api/voice/agent"| ROUTES
```

---

## 4. Pipeline Processing Flow

```mermaid
flowchart TD
    A["Voice Agent Endpoint"] --> B["Read & Validate Audio"]
    B --> C{"Audio Valid?"}
    C -->|"No / Invalid"| E["HTTP 400/415 Error"]
    C -->|"Yes"| D["STT Transcribe (Gnani)"]
    D --> F{"Transcript Non-Empty?"}
    F -->|"No"| G["HTTP 422: No speech detected"]
    F -->|"Yes"| H["Guardrail Check"]
    H --> I{"Risk Score = 1?"}
    I -->|"Yes (Blocked)"| J["Return Blocked Reply<br/>No memory write"]
    I -->|"No"| K{"Churn Risk > 0.85?"}
    K -->|"Yes (Escalate)"| L["Generate Escalation Reply<br/>action = escalate_to_human"]
    K -->|"No (Normal)"| M["Fetch Chat History"]
    M --> N["Append HumanMessage"]
    N --> O["Intent Routing"]
    O --> P{"SystemOne Confident?"}
    P -->|"Yes"| Q["Execute Relevant Tool"]
    P -->|"No"| R["SML Intent Routing"]
    R --> Q
    Q --> S{"Tool Execution<br/>Success?"}
    S -->|"Yes"| T["Build Reply Input<br/>(message + TOOL_RESULT)"]
    S -->|"No"| U["Tool Error Reply"]
    T --> V["LLM Reply Generation"]
    U --> V
    V --> W["Persist Checkpoint"]
    W --> X["TTS Synthesize (Gnani)"]
    X --> Y["Return WAV + Headers"]
    J --> Y
    L --> Y
```

---

## 5. Routing & Tool Decision Flow

```mermaid
flowchart TD
    A["handle_message<br/>(thread_id, message)"] --> B["Guardrail:<br/>risk_score, churn_risk"]
    B --> C{"Risk Score = 1?"}
    C -->|"Blocked"| D["Return Blocked Reply"]
    C -->|"No"| E{"Churn Risk > 0.85?"}
    E -->|"Escalate"| F["action = escalate_to_human<br/>Generate human reply"]
    E -->|"Normal"| G["Build Conversation"]
    G --> H["Intent Routing"]
    H --> I{"SystemOne Route<br/>Confident?"}
    I -->|"Yes"| J["action = Selected Action"]
    I -->|"No"| K["slm_route: SML Intent Routing"]
    K --> L["action = Selected Action<br/>(with escalation exposed)"]
    J --> M["_run_operation:<br/>Execute Tool"]
    L --> M
    M --> N{"Tool Executes<br/>Successfully?"}
    N -->|"Yes"| O["Return Tool Result"]
    N -->|"No"| P["Return Tool Error"]
    O --> Q["Build Reply Input"]
    P --> Q
    Q --> R["LLM Reply Generation"]
    R --> S["Persist Checkpoint"]
    S --> T["Return Reply + Action"]
    D --> T
    F --> T
```

---

## 6. Service Stack & Dependency Summary

| Layer | Component | Technology | Responsibility |
|-------|-----------|------------|----------------|
| **Client** | Browser / Vite Frontend | React 19, Next.js, TailwindCSS, WAV codec | Voice input, recording, WAV conversion, playback, conversation UI |
| **Backend** | FastAPI | Python 3.12, FastAPI, Uvicorn, LangGraph | API routing, pipeline orchestration, safety & routing |
| **Orchestration** | LangGraph | LangGraph, MongoDB Checkpoints | Conversation state management, checkpoint persistence |
| **Safety** | Guardrails | SystemOne/Noul | Risk & churn assessment, content blocking |
| **Routing** | SystemOne / Laya | SystemOne / Laya | Intent routing, entity recognition |
| **Generation** | OpenAI-Compatible | OpenAI-compatible API | Customer reply generation |
| **Voice** | Gnani STT/TTS | Gnani API | Audio transcription & synthesis |
| **Storage** | MongoDB | MongoDB 7.0 | Order/user data, conversation checkpoints |
| **Docker** | docker-compose | Docker Compose | Full-stack orchestration & deployment |

---

## 7. API Endpoint Summary

| Method | Endpoint | Purpose |
|-------|----------|---------|
| `GET` | `/api/health` | Backend health check |
| `GET` | `/api/profile` | Current user profile |
| `GET` | `/api/orders` | Current user's orders |
| `GET` | `/api/orders/{order_id}` | Single order detail |
| `POST` | `/api/voice/agent/{session_id}` | Audio turn: STT → pipeline → TTS (returns WAV audio + headers) |