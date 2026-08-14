import { useState } from "react";
import type { LatencyMetrics } from "@/types/api";

const PRIMARY: Array<[keyof LatencyMetrics, string]> = [
  ["stt", "STT"],
  ["dense_retrieval", "Retrieval"],
  ["rerank", "Rerank"],
  ["llm", "LLM"],
];

const DETAIL: Array<[keyof LatencyMetrics, string]> = [
  ["embedding", "Embedding"],
  ["bm25", "BM25"],
  ["fusion", "Fusion"],
  ["grounding", "Grounding"],
];

function Metric({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-border py-2">
      <span className="label-mono">{label}</span>
      <span className="font-mono text-sm text-foreground">
        {typeof value === "number" ? `${Math.round(value)} ms` : "—"}
      </span>
    </div>
  );
}

export function LatencyPanel({ latency }: { latency: LatencyMetrics }) {
  const [open, setOpen] = useState(false);
  return (
    <section aria-labelledby="latency-heading" className="border-t border-border py-6">
      <h2 id="latency-heading" className="label-mono">
        Latency
      </h2>
      <div className="mt-3 grid gap-x-8 sm:grid-cols-2">
        {PRIMARY.map(([key, label]) => (
          <Metric key={key} label={label} value={latency[key]} />
        ))}
        {open &&
          DETAIL.map(([key, label]) => <Metric key={key} label={label} value={latency[key]} />)}
      </div>
      <div className="mt-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className="label-mono rounded-xs border border-border px-2 py-1 hover:border-border-strong hover:text-foreground"
        >
          {open ? "Hide technical details" : "Technical details"}
        </button>
        <p className="font-mono text-sm">
          <span className="label-mono mr-2">Total</span>
          {typeof latency.total === "number" ? `${Math.round(latency.total)} ms` : "—"}
        </p>
      </div>
    </section>
  );
}
