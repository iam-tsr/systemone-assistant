"use client";

import { useCallback, useRef, useState } from "react";

import type { PersonaState } from "@/components/ai-elements/persona";

export type VoiceStatus = "idle" | "recording" | "transcribing" | "speaking" | "error";

type TranscriptResult = { transcript: string; request_id: string | null };

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`;
}

async function transcribeBlob(blob: Blob, filename: string): Promise<string> {
  const form = new FormData();
  form.append("file", blob, filename);
  const res = await fetch("/api/voice/stt", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  const data = (await res.json()) as TranscriptResult;
  return data.transcript;
}

async function speak(text: string): Promise<void> {
  const res = await fetch("/api/voice/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, voice: "Pranav" }),
  });
  if (!res.ok) throw new Error(await readError(res));
  const url = URL.createObjectURL(await res.blob());
  const audio = new Audio(url);
  await audio.play();
  await new Promise<void>((resolve) => {
    audio.onended = () => resolve();
  });
  URL.revokeObjectURL(url);
}

// Map the voice pipeline phase onto the Persona animation state.
export function personaStateFor(status: VoiceStatus): PersonaState {
  switch (status) {
    case "recording":
      return "listening";
    case "transcribing":
      return "thinking";
    case "speaking":
      return "speaking";
    default:
      return "idle";
  }
}

export function useVoiceLoop() {
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        setStatus("transcribing");
        try {
          const text = await transcribeBlob(blob, "utterance.webm");
          setTranscript(text);
          if (text.trim()) {
            setStatus("speaking");
            await speak(text);
          }
          setStatus("idle");
        } catch (err) {
          setError(err instanceof Error ? err.message : "Voice request failed");
          setStatus("error");
        }
      };
      recorder.start();
      recorderRef.current = recorder;
      setStatus("recording");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Microphone unavailable");
      setStatus("error");
    }
  }, []);

  const stop = useCallback(() => {
    recorderRef.current?.stop();
    recorderRef.current = null;
  }, []);

  return { status, transcript, error, start, stop };
}
