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
  const getNum = (v: number | null | undefined): number | undefined =>
    typeof v === "number" ? v : undefined;

  if (key === "total") return getNum(latency.total) ?? getNum(latency.total_backend_ms);
  if (key === "stt") return getNum(latency.stt) ?? getNum(latency.stt_ms);
  if (key === "dense_retrieval")
    return getNum(latency.dense_retrieval) ?? getNum(latency.dense_retrieval_ms);
  if (key === "rerank") return getNum(latency.rerank) ?? getNum(latency.reranking_ms);
  if (key === "llm") return getNum(latency.llm) ?? getNum(latency.llm_ms);
  if (key === "embedding") return getNum(latency.embedding) ?? getNum(latency.embedding_ms);
  if (key === "bm25") return getNum(latency.bm25) ?? getNum(latency.bm25_ms);
  if (key === "fusion") return getNum(latency.fusion) ?? getNum(latency.fusion_ms);
  if (key === "context_building") return getNum(latency.context_building_ms);
  if (key === "grounding") return getNum(latency.grounding) ?? getNum(latency.grounding_ms);
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
