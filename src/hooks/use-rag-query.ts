import { useCallback, useRef, useState } from "react";
import { ragApi } from "@/lib/api";
import { RagApiError, type LanguageCode, type RagResponse } from "@/types/api";
import type { RecorderState } from "@/types/audio";

export function useRagQuery() {
  const [state, setState] = useState<RecorderState>("IDLE");
  const [result, setResult] = useState<RagResponse | null>(null);
  const [error, setError] = useState<RagApiError | null>(null);
  const inFlight = useRef(false);

  const run = useCallback(async (fn: () => Promise<RagResponse>, hasAudio: boolean) => {
    if (inFlight.current) return;
    inFlight.current = true;
    setError(null);
    setResult(null);
    const stages: RecorderState[] = hasAudio
      ? ["UPLOADING", "TRANSCRIBING", "RETRIEVING", "GENERATING", "VERIFYING"]
      : ["RETRIEVING", "GENERATING", "VERIFYING"];
    let i = 0;
    setState(stages[0]!);
    const ticker = setInterval(() => {
      i = Math.min(i + 1, stages.length - 1);
      setState(stages[i]!);
    }, 900);
    try {
      const res = await fn();
      if (!res.success && res.error) {
        throw new RagApiError(res.error.code === "STT_FAILED" ? "STT_FAILED" : "UNKNOWN");
      }
      setResult(res);
      setState("SUCCESS");
    } catch (err) {
      setError(err instanceof RagApiError ? err : new RagApiError("UNKNOWN"));
      setState("ERROR");
    } finally {
      clearInterval(ticker);
      inFlight.current = false;
    }
  }, []);

  const submitVoice = useCallback(
    (audio: Blob, language: LanguageCode) =>
      run(() => ragApi.voiceQuery(audio, language), true),
    [run],
  );

  const submitText = useCallback(
    (query: string, language: LanguageCode) =>
      run(() => ragApi.textQuery(query, language), false),
    [run],
  );

  const fail = useCallback((err: RagApiError) => {
    setError(err);
    setResult(null);
    setState("ERROR");
  }, []);

  const reset = useCallback(() => {
    setState("IDLE");
    setError(null);
    setResult(null);
  }, []);

  return { state, setState, result, error, submitVoice, submitText, fail, reset };
}
