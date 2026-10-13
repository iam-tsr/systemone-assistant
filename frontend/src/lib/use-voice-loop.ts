"use client";

import { useCallback, useRef, useState } from "react";

import type { PersonaState } from "@/components/ai-elements/persona";

export type VoiceStatus = "idle" | "recording" | "transcribing" | "speaking" | "error";
export type VoiceTurn = { transcript: string; reply: string };

async function readError(res: Response): Promise<string> {
  const body = await res.json().catch(() => null);
  return typeof body?.detail === "string" ? body.detail : `Request failed (${res.status})`;
}

function encodeWav(buffer: AudioBuffer): Blob {
  const channelCount = buffer.numberOfChannels;
  const frameCount = buffer.length;
  const wav = new ArrayBuffer(44 + frameCount * channelCount * 2);
  const view = new DataView(wav);
  const write = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };
  write(0, "RIFF");
  view.setUint32(4, 36 + frameCount * channelCount * 2, true);
  write(8, "WAVE");
  write(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channelCount, true);
  view.setUint32(24, buffer.sampleRate, true);
  view.setUint32(28, buffer.sampleRate * channelCount * 2, true);
  view.setUint16(32, channelCount * 2, true);
  view.setUint16(34, 16, true);
  write(36, "data");
  view.setUint32(40, frameCount * channelCount * 2, true);

  const channels = Array.from({ length: channelCount }, (_, index) =>
    buffer.getChannelData(index),
  );
  let offset = 44;
  for (let frame = 0; frame < frameCount; frame += 1) {
    for (let channel = 0; channel < channelCount; channel += 1) {
      const sample = Math.max(-1, Math.min(1, channels[channel][frame]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
      offset += 2;
    }
  }
  return new Blob([wav], { type: "audio/wav" });
}

async function toWav(blob: Blob): Promise<Blob> {
  const context = new AudioContext();
  try {
    const buffer = await context.decodeAudioData(await blob.arrayBuffer());
    return encodeWav(buffer);
  } finally {
    await context.close();
  }
}

async function requestVoiceAgent(blob: Blob): Promise<{ transcript: string; reply: string; audio: Blob }> {
  const form = new FormData();
  form.append("file", await toWav(blob), "utterance.wav");
  const res = await fetch("/api/voice/agent", { method: "POST", body: form });
  if (!res.ok) throw new Error(await readError(res));
  return {
    transcript: decodeURIComponent(res.headers.get("X-Transcript") ?? ""),
    reply: decodeURIComponent(res.headers.get("X-Reply") ?? ""),
    audio: await res.blob(),
  };
}

async function playAudio(blob: Blob): Promise<void> {
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  try {
    await audio.play();
    await new Promise<void>((resolve, reject) => {
      audio.onended = () => resolve();
      audio.onerror = () => reject(new Error("Unable to play the assistant response"));
    });
  } finally {
    URL.revokeObjectURL(url);
  }
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

export function useVoiceLoop(onTurn?: (turn: VoiceTurn) => void) {
  const [status, setStatus] = useState<VoiceStatus>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const monitorRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : undefined;
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);
      chunksRef.current = [];
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024;
      audioContext.createMediaStreamSource(stream).connect(analyser);
      const samples = new Uint8Array(analyser.fftSize);
      let heardSpeech = false;
      let silentSince: number | null = null;
      const startedAt = performance.now();

      const monitor = () => {
        analyser.getByteTimeDomainData(samples);
        const level = Math.sqrt(
          samples.reduce((sum, sample) => sum + (sample - 128) ** 2, 0) / samples.length,
        );
        const now = performance.now();
        if (level > 8) {
          heardSpeech = true;
          silentSince = null;
        } else if (heardSpeech) {
          silentSince ??= now;
          if (now - silentSince >= 900 || now - startedAt >= 15000) {
            if (recorder.state === "recording") recorder.stop();
            return;
          }
        } else if (now - startedAt >= 15000) {
          if (recorder.state === "recording") recorder.stop();
          return;
        }
        monitorRef.current = requestAnimationFrame(monitor);
      };

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        if (monitorRef.current !== null) cancelAnimationFrame(monitorRef.current);
        await audioContext.close();
        stream.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType });
        setStatus("transcribing");
        try {
          const result = await requestVoiceAgent(blob);
          setTranscript(result.transcript);
          onTurn?.({ transcript: result.transcript, reply: result.reply });
          if (result.transcript.trim()) {
            setStatus("speaking");
            await playAudio(result.audio);
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
      monitorRef.current = requestAnimationFrame(monitor);
    } catch (err) {
      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
      setError(err instanceof Error ? err.message : "Microphone unavailable");
      setStatus("error");
    }
  }, []);

  const stop = useCallback(() => {
    if (monitorRef.current !== null) cancelAnimationFrame(monitorRef.current);
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    recorderRef.current = null;
    streamRef.current?.getTracks().forEach((track) => track.stop());
  }, []);

  return { status, transcript, error, start, stop };
}
