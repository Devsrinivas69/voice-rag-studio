import { useState } from "react";
import type { LatencyMetrics } from "@/types/api";

const PRIMARY: Array<[string, string]> = [
  ["stt", "STT (Sarvam)"],
  ["dense_retrieval", "Dense Search"],
  ["rerank", "Reranker"],
  ["llm", "LLM (Gemini)"],
];

const DETAIL: Array<[string, string]> = [
  ["embedding", "Embedding"],
  ["bm25", "Sparse BM25"],
  ["fusion", "RRF Fusion"],
  ["context_building", "Context Building"],
  ["grounding", "Grounding Eval"],
];

function getValue(latency: LatencyMetrics, key: string): number | undefined {
  if (key === "total") return latency.total ?? latency.total_backend_ms;
  if (key === "stt") return latency.stt ?? latency.stt_ms;
  if (key === "dense_retrieval") return latency.dense_retrieval ?? latency.dense_retrieval_ms;
  if (key === "rerank") return latency.rerank ?? latency.reranking_ms;
  if (key === "llm") return latency.llm ?? latency.llm_ms;
  if (key === "embedding") return latency.embedding ?? latency.embedding_ms;
  if (key === "bm25") return latency.bm25 ?? latency.bm25_ms;
  if (key === "fusion") return latency.fusion ?? latency.fusion_ms;
  if (key === "context_building") return latency.context_building_ms;
  if (key === "grounding") return latency.grounding ?? latency.grounding_ms;
  return undefined;
}

function Metric({ label, value }: { label: string; value: number | undefined }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-border py-2">
      <span className="label-mono">{label}</span>
      <span className="font-mono text-sm text-foreground">
        {typeof value === "number" ? `${Math.round(value)} ms` : "0 ms"}
      </span>
    </div>
  );
}

export function LatencyPanel({ latency }: { latency: LatencyMetrics }) {
  const [open, setOpen] = useState(false);
  const totalVal = getValue(latency, "total");

  return (
    <section aria-labelledby="latency-heading" className="border-t border-border py-6">
      <h2 id="latency-heading" className="label-mono">
        Stage Latency Breakdown
      </h2>
      <div className="mt-3 grid gap-x-8 sm:grid-cols-2">
        {PRIMARY.map(([key, label]) => (
          <Metric key={key} label={label} value={getValue(latency, key)} />
        ))}
        {open &&
          DETAIL.map(([key, label]) => (
            <Metric key={key} label={label} value={getValue(latency, key)} />
          ))}
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
          {typeof totalVal === "number" ? `${Math.round(totalVal)} ms` : "0 ms"}
        </p>
      </div>
    </section>
  );
}
