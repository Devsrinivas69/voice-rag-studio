import type { RecorderState } from "@/types/audio";

export const STAGES = [
  "Voice",
  "STT",
  "Query",
  "Hybrid retrieval",
  "Rerank",
  "Generate",
  "Verify",
] as const;

type StageStatus = "idle" | "processing" | "complete" | "error";

function stageIndex(state: RecorderState): number {
  switch (state) {
    case "RECORDING":
    case "STOPPING":
      return 0;
    case "UPLOADING":
    case "TRANSCRIBING":
      return 1;
    case "RETRIEVING":
      return 3;
    case "GENERATING":
      return 5;
    case "VERIFYING":
      return 6;
    default:
      return -1;
  }
}

export function PipelineStatus({ state }: { state: RecorderState }) {
  const active = stageIndex(state);
  const done = state === "SUCCESS";
  const errored = state === "ERROR";

  const statusFor = (i: number): StageStatus => {
    if (done) return "complete";
    if (errored) return i <= Math.max(active, 0) ? "error" : "idle";
    if (active < 0) return "idle";
    if (i < active) return "complete";
    if (i === active) return "processing";
    return "idle";
  };

  return (
    <section aria-labelledby="pipeline-heading" className="border-t border-border py-6">
      <h2 id="pipeline-heading" className="label-mono">
        Pipeline
      </h2>
      <ol className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-0">
        {STAGES.map((stage, i) => {
          const status = statusFor(i);
          return (
            <li key={stage} className="flex items-center gap-2 sm:flex-1">
              <span
                className={`flex w-full items-center gap-2 border px-2.5 py-1.5 font-mono text-[0.625rem] tracking-[0.14em] uppercase transition-colors ${
                  status === "processing"
                    ? "border-primary text-primary"
                    : status === "complete"
                      ? "border-success/40 text-success"
                      : status === "error"
                        ? "border-destructive/50 text-destructive"
                        : "border-border text-muted-foreground"
                }`}
              >
                <span
                  aria-hidden="true"
                  className={`size-1.5 shrink-0 rounded-full ${
                    status === "processing"
                      ? "animate-pulse bg-primary"
                      : status === "complete"
                        ? "bg-success"
                        : status === "error"
                          ? "bg-destructive"
                          : "bg-border-strong"
                  }`}
                />
                <span className="truncate">{stage}</span>
                <span className="sr-only">: {status}</span>
              </span>
              {i < STAGES.length - 1 && (
                <span aria-hidden="true" className="hidden text-muted-foreground sm:inline">
                  ›
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
