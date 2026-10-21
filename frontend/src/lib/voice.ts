"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { apiUrl } from "@/lib/api";

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

async function requestVoiceAgent(
  blob: Blob,
  sessionId: string,
  signal?: AbortSignal,
): Promise<{ transcript: string; reply: string; audio: Blob }> {
  const form = new FormData();
  form.append("file", await toWav(blob), "utterance.wav");
  const res = await fetch(apiUrl(`/api/voice/agent/${encodeURIComponent(sessionId)}`), {
    method: "POST",
    body: form,
    signal,
  });
  if (!res.ok) throw new Error(await readError(res));
  return {
    transcript: decodeURIComponent(res.headers.get("X-Transcript") ?? ""),
    reply: decodeURIComponent(res.headers.get("X-Reply") ?? ""),
    audio: await res.blob(),
  };
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
  const [active, setActive] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const onTurnRef = useRef(onTurn);
  onTurnRef.current = onTurn;

  const activeRef = useRef(false);
  const cancelledRef = useRef(false);
  const segmentIdRef = useRef(0);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const monitorRef = useRef<number | null>(null);
  const restartTimerRef = useRef<number | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlRef = useRef<string | null>(null);

  const clearRestartTimer = useCallback(() => {
    if (restartTimerRef.current !== null) {
      window.clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
  }, []);

  const stopAudio = useCallback(() => {
    const el = audioElRef.current;
    if (el) {
      el.pause();
      el.src = "";
      try {
        el.load();
      } catch {
        // ignore
      }
    }
    audioElRef.current = null;
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
  }, []);

  const playAudioCancellable = useCallback(async (blob: Blob): Promise<void> => {
    if (blob.size < 100) return;
    const url = URL.createObjectURL(blob);
    audioUrlRef.current = url;
    const audio = new Audio(url);
    audioElRef.current = audio;
    await audio.play();
    await new Promise<void>((resolve, reject) => {
      const onEnd = () => {
        cleanup();
        resolve();
      };
      const onErr = () => {
        cleanup();
        reject(new Error("Unable to play the assistant response"));
      };
      const cleanup = () => {
        audio.removeEventListener("ended", onEnd);
        audio.removeEventListener("error", onErr);
      };
      audio.addEventListener("ended", onEnd, { once: true });
      audio.addEventListener("error", onErr, { once: true });
    });
    if (audioUrlRef.current === url) {
      URL.revokeObjectURL(url);
      audioUrlRef.current = null;
    }
    audioElRef.current = null;
  }, []);

  const cleanupSegment = useCallback(() => {
    if (monitorRef.current !== null) {
      cancelAnimationFrame(monitorRef.current);
      monitorRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    recorderRef.current = null;
  }, []);

  // Forward-declare so startSegment and scheduleRestart can reference each other via refs
  const startSegmentRef = useRef<() => Promise<void>>(async () => {});

  const scheduleRestart = useCallback(
    (delayMs: number) => {
      if (!activeRef.current || cancelledRef.current) return;
      clearRestartTimer();
      restartTimerRef.current = window.setTimeout(() => {
        restartTimerRef.current = null;
        if (!activeRef.current || cancelledRef.current) return;
        void startSegmentRef.current();
      }, delayMs);
    },
    [clearRestartTimer],
  );

  const startSegment = useCallback(async () => {
    if (!activeRef.current || cancelledRef.current) return;
    if (recorderRef.current?.state === "recording") return;

    const thisSegment = ++segmentIdRef.current;
    setError(null);

    let chunks: Blob[] = [];
    let audioContext: AudioContext | null = null;
    let stream: MediaStream | null = null;

    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!activeRef.current || cancelledRef.current || thisSegment !== segmentIdRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      streamRef.current = stream;

      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : MediaRecorder.isTypeSupported("audio/webm")
          ? "audio/webm"
          : undefined;
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

      audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024;
      audioContext.createMediaStreamSource(stream).connect(analyser);
      const samples = new Uint8Array(analyser.fftSize);
      let heardSpeech = false;
      let silentSince: number | null = null;
      const startedAt = performance.now();

      const monitor = () => {
        if (!activeRef.current || cancelledRef.current || thisSegment !== segmentIdRef.current) return;
        analyser.getByteTimeDomainData(samples);
        const level = Math.sqrt(
          samples.reduce((sum, s) => sum + (s - 128) ** 2, 0) / samples.length,
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
        if (e.data.size > 0) chunks.push(e.data);
      };

      recorder.onstop = async () => {
        if (monitorRef.current !== null) {
          cancelAnimationFrame(monitorRef.current);
          monitorRef.current = null;
        }
        if (audioContext && audioContextRef.current === audioContext) {
          audioContext.close().catch(() => {});
          audioContextRef.current = null;
        }
        // segment mic is done — release tracks so next segment gets a fresh one
        stream?.getTracks().forEach((t) => t.stop());
        if (streamRef.current === stream) streamRef.current = null;
        recorderRef.current = null;

        if (cancelledRef.current || !activeRef.current || thisSegment !== segmentIdRef.current) return;

        const blob = new Blob(chunks, { type: recorder.mimeType });
        const isSilent = !heardSpeech || blob.size < 800;
        if (isSilent) {
          if (activeRef.current && !cancelledRef.current) {
            setStatus("recording");
            scheduleRestart(250);
          } else {
            setStatus("idle");
          }
          return;
        }

        setStatus("transcribing");
        const ac = new AbortController();
        abortRef.current = ac;
        try {
          sessionIdRef.current ??= crypto.randomUUID();
          const result = await requestVoiceAgent(blob, sessionIdRef.current, ac.signal);
          if (cancelledRef.current || !activeRef.current || thisSegment !== segmentIdRef.current) return;
          setTranscript(result.transcript);
          onTurnRef.current?.({ transcript: result.transcript, reply: result.reply });
          if (result.transcript.trim() && result.audio.size > 100) {
            setStatus("speaking");
            await playAudioCancellable(result.audio);
            if (cancelledRef.current || !activeRef.current) return;
          }
          if (activeRef.current && !cancelledRef.current && thisSegment === segmentIdRef.current) {
            setStatus("recording");
            scheduleRestart(350);
          } else {
            setStatus("idle");
          }
        } catch (err) {
          if ((err as DOMException)?.name === "AbortError") return;
          if (cancelledRef.current || !activeRef.current) return;
          setError(err instanceof Error ? err.message : "Voice request failed");
          setStatus("error");
          if (activeRef.current && !cancelledRef.current) scheduleRestart(900);
        } finally {
          if (abortRef.current === ac) abortRef.current = null;
        }
      };

      recorder.start();
      recorderRef.current = recorder;
      setStatus("recording");
      monitorRef.current = requestAnimationFrame(monitor);
    } catch (err) {
      if (!activeRef.current || cancelledRef.current) return;
      cleanupSegment();
      setError(err instanceof Error ? err.message : "Microphone unavailable");
      setStatus("error");
      activeRef.current = false;
      setActive(false);
    }
  }, [cleanupSegment, playAudioCancellable, scheduleRestart]);

  startSegmentRef.current = startSegment;

  const start = useCallback(async () => {
    if (activeRef.current) return;
    cancelledRef.current = false;
    activeRef.current = true;
    setActive(true);
    setError(null);
    segmentIdRef.current += 1;
    clearRestartTimer();
    await startSegment();
  }, [clearRestartTimer, startSegment]);

  const stop = useCallback(() => {
    cancelledRef.current = true;
    activeRef.current = false;
    setActive(false);
    segmentIdRef.current += 1;
    clearRestartTimer();
    if (monitorRef.current !== null) {
      cancelAnimationFrame(monitorRef.current);
      monitorRef.current = null;
    }
    abortRef.current?.abort();
    abortRef.current = null;
    const rec = recorderRef.current;
    if (rec?.state === "recording") {
      try {
        rec.stop();
      } catch {
        // ignore
      }
    }
    stopAudio();
    cleanupSegment();
    setStatus("idle");
    // allow next start() immediately
    window.setTimeout(() => {
      cancelledRef.current = false;
    }, 0);
  }, [cleanupSegment, clearRestartTimer, stopAudio]);

  useEffect(() => {
    return () => {
      cancelledRef.current = true;
      activeRef.current = false;
      clearRestartTimer();
      if (monitorRef.current !== null) cancelAnimationFrame(monitorRef.current);
      abortRef.current?.abort();
      stopAudio();
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, [clearRestartTimer, stopAudio]);

  return { status, active, transcript, error, start, stop };
}
