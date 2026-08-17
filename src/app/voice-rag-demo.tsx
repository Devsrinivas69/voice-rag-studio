"use client";

import { useCallback, useEffect, useState } from "react";
import { Header } from "@/components/header";
import { VoiceRecorder } from "@/components/voice-recorder";
import { LanguageSelector } from "@/components/language-selector";
import { TranscriptPanel } from "@/components/transcript-panel";
import { AnswerPanel } from "@/components/answer-panel";
import { SourcesPanel } from "@/components/sources-panel";
import { LatencyPanel } from "@/components/latency-panel";
import { PipelineStatus } from "@/components/pipeline-status";
import { RequestId } from "@/components/request-id";
import { ExamplePrompts } from "@/components/example-prompts";
import { ErrorState } from "@/components/error-state";
import { TextFallback } from "@/components/text-fallback";
import { useVoiceRecorder } from "@/hooks/use-voice-recorder";
import { useRagQuery } from "@/hooks/use-rag-query";
import { ragApi } from "@/lib/api";
import { isRecordingSupported } from "@/lib/audio";
import { STATE_LABELS } from "@/types/audio";
import type { LanguageCode, RagApiError } from "@/types/api";

export function VoiceRagDemo() {
  const [language, setLanguage] = useState<LanguageCode>("en-IN");
  const [textQuery, setTextQuery] = useState("");
  const [online, setOnline] = useState<boolean | null>(null);
  const [supported, setSupported] = useState(true);

  const { state, result, error, submitVoice, submitText, fail, reset } = useRagQuery();

  useEffect(() => {
    setSupported(isRecordingSupported());
    void ragApi.healthCheck().then(setOnline);
  }, []);

  const onComplete = useCallback(
    (blob: Blob) => {
      void submitVoice(blob, language);
    },
    [submitVoice, language],
  );

  const onError = useCallback((err: RagApiError) => fail(err), [fail]);

  const recorder = useVoiceRecorder({ onComplete, onError });

  const busy = !["IDLE", "SUCCESS", "ERROR"].includes(state) || recorder.isRecording;
  const displayState = recorder.isRecording ? "RECORDING" : state;

  const notEnoughEvidence = result != null && result.should_answer === false && !result.blocked;
  const blocked = result?.blocked === true;
  const hasAnswer = result != null && !notEnoughEvidence && !blocked && result.answer.length > 0;

  return (
    <div className="min-h-screen">
      <Header online={online} />

      <main className="mx-auto max-w-6xl px-4 pb-24 sm:px-6">
        <section className="border-b border-border py-16 text-center sm:py-20">
          <p className="label-mono">Hacker House Goa 2026 · Independent demo</p>
          <h1 className="mt-5 font-display text-5xl leading-[1.02] sm:text-7xl">
            Ask the dataset.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-balance text-muted-foreground">
            Speak naturally. Retrieve relevant evidence. Get a grounded answer.
          </p>
          <p className="label-mono mt-3">Voice-enabled retrieval augmented generation</p>

          <div className="mt-12 flex flex-col items-center gap-6">
            <VoiceRecorder
              state={displayState}
              isRecording={recorder.isRecording}
              elapsedMs={recorder.elapsedMs}
              levels={recorder.levels}
              supported={supported}
              onStart={() => void recorder.start()}
              onStop={recorder.stop}
              onCancel={recorder.cancel}
              onReset={reset}
            />
            <LanguageSelector value={language} onChange={setLanguage} disabled={busy} />
          </div>

          <p aria-live="polite" className="sr-only">
            {STATE_LABELS[displayState]}
          </p>
        </section>

        <div className="grid gap-x-12 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
          <div>
            {result?.transcript && <TranscriptPanel transcript={result.transcript} />}

            {hasAnswer && result && <AnswerPanel result={result} />}

            {notEnoughEvidence && (
              <ErrorState
                variant="no-evidence"
                title="Not enough evidence"
                message="I couldn't find enough relevant information in the provided dataset to answer that reliably."
              />
            )}

            {blocked && (
              <ErrorState
                variant="guardrail"
                title="Request blocked"
                message="That request could not be processed safely."
              />
            )}

            {error && (
              <ErrorState title="Something went wrong" message={error.message} onRetry={reset} />
            )}

            {result && result.sources.length > 0 && <SourcesPanel sources={result.sources} />}

            {!result && !error && <ExamplePrompts onPick={setTextQuery} />}

            <TextFallback
              value={textQuery}
              onChange={setTextQuery}
              disabled={busy}
              onSubmit={() => void submitText(textQuery.trim(), language)}
            />
          </div>

          <aside>
            <PipelineStatus state={displayState} />
            {result && <LatencyPanel latency={result.latency} />}
            {result?.request_id && <RequestId id={result.request_id} />}
          </aside>
        </div>
      </main>
    </div>
  );
}
