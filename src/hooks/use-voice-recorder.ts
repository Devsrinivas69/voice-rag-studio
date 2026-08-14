import { useCallback, useEffect, useRef, useState } from "react";
import { isRecordingSupported, pickMimeType } from "@/lib/audio";
import { MAX_RECORDING_MS } from "@/types/audio";
import { RagApiError } from "@/types/api";

interface Options {
  onComplete: (blob: Blob) => void;
  onError: (error: RagApiError) => void;
}

export function useVoiceRecorder({ onComplete, onError }: Options) {
  const [isRecording, setIsRecording] = useState(false);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [level, setLevels] = useState<number[]>([]);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const rafRef = useRef<number | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const maxTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelledRef = useRef(false);

  const cleanup = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
    if (maxTimeoutRef.current) clearTimeout(maxTimeoutRef.current);
    maxTimeoutRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    void audioCtxRef.current?.close().catch(() => undefined);
    audioCtxRef.current = null;
    recorderRef.current = null;
    setLevels([]);
    setIsRecording(false);
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const start = useCallback(async () => {
    if (recorderRef.current) return;
    if (!isRecordingSupported()) {
      onError(new RagApiError("UNSUPPORTED"));
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError(new RagApiError("MIC_DENIED"));
      return;
    }
    cancelledRef.current = false;
    streamRef.current = stream;

    const mimeType = pickMimeType();
    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    } catch {
      cleanup();
      onError(new RagApiError("UNSUPPORTED"));
      return;
    }
    recorderRef.current = recorder;
    const chunks: Blob[] = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };
    recorder.onerror = () => {
      cleanup();
      onError(new RagApiError("UNKNOWN", "Recording failed. Please try again."));
    };
    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType ?? "audio/webm" });
      const wasCancelled = cancelledRef.current;
      cleanup();
      if (wasCancelled) return;
      if (blob.size < 1024) {
        onError(new RagApiError("EMPTY_AUDIO"));
        return;
      }
      onComplete(blob);
    };

    // Live level analysis (real mic data only).
    try {
      const Ctx: typeof AudioContext =
        window.AudioContext ??
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new Ctx();
      audioCtxRef.current = ctx;
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      ctx.createMediaStreamSource(stream).connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (const v of data) sum += (v - 128) ** 2;
        const rms = Math.sqrt(sum / data.length) / 128;
        setLevels((prev) => [...prev.slice(-47), Math.min(1, rms * 3)]);
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch {
      /* graceful fallback: no waveform */
    }

    recorder.start();
    setIsRecording(true);
    setElapsedMs(0);
    const startedAt = Date.now();
    timerRef.current = setInterval(() => setElapsedMs(Date.now() - startedAt), 200);
    maxTimeoutRef.current = setTimeout(() => {
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    }, MAX_RECORDING_MS);
  }, [cleanup, onComplete, onError]);

  const stop = useCallback(() => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  }, []);

  const cancel = useCallback(() => {
    cancelledRef.current = true;
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    else cleanup();
  }, [cleanup]);

  return { isRecording, elapsedMs, levels: level, start, stop, cancel };
}
