"use client";

import { useEffect, useState } from "react";
import { Header } from "@/components/header";
import { ragApi } from "@/lib/api";

const SECTIONS = [
  {
    n: "01",
    title: "Voice Input",
    body: "The browser captures microphone audio with MediaRecorder, negotiating the best supported codec (Opus in WebM, falling back to MP4). Audio is held in memory only and never persisted.",
  },
  {
    n: "02",
    title: "Speech Recognition",
    body: "The audio blob is posted to FastAPI as multipart form data with a language code. Sarvam STT returns a transcript in the selected Indic language.",
  },
  {
    n: "03",
    title: "Query Processing",
    body: "The transcript is normalised, checked against guardrails for prompt injection, and embedded for dense retrieval.",
  },
  {
    n: "04",
    title: "Hybrid Retrieval",
    body: "BM25 lexical search runs alongside vector search over the Qdrant index. Results are merged with reciprocal rank fusion for lexical precision plus semantic recall.",
  },
  {
    n: "05",
    title: "Reranking",
    body: "A cross-encoder reorders fused candidates so only the highest-signal chunks reach the generation context window.",
  },
  {
    n: "06",
    title: "Generation",
    body: "The LLM answers strictly from the retrieved evidence. Off-topic queries return should_answer=false instead of a hallucinated answer.",
  },
  {
    n: "07",
    title: "Grounding",
    body: "Each claim is verified against the retrieved chunks. The frontend surfaces the result as a grounded or not-grounded status with supporting evidence.",
  },
  {
    n: "08",
    title: "Latency",
    body: "Every stage is timed server-side and returned with the response. The frontend displays only measured values; missing metrics render as an em dash.",
  },
];

const FLOW = [
  "Voice",
  "Sarvam STT",
  "Query",
  "BM25 + Vector search",
  "RRF fusion",
  "Reranking",
  "LLM",
  "Grounding",
];

export function ArchitectureView() {
  const [online, setOnline] = useState<boolean | null>(null);
  useEffect(() => {
    void ragApi.healthCheck().then(setOnline);
  }, []);

  return (
    <div className="min-h-screen">
      <Header online={online} />
      <main className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <p className="label-mono">Task 02 / Voice-enabled RAG</p>
        <h1 className="mt-4 font-display text-5xl leading-[1.05] sm:text-6xl">
          System architecture.
        </h1>
        <p className="mt-4 max-w-2xl text-muted-foreground">
          An independent demo project. Informational only — no retrieval runs on this page.
        </p>

        <section
          aria-label="Pipeline diagram"
          className="mt-12 border border-border bg-card/40 p-6"
        >
          <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {FLOW.map((step, i) => (
              <li key={step} className="flex items-center gap-3">
                <span className="flex w-full items-center gap-3 border border-border px-3 py-3">
                  <span className="font-mono text-[0.625rem] text-primary">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="font-mono text-xs tracking-wide">{step}</span>
                </span>
              </li>
            ))}
          </ol>
          <svg
            viewBox="0 0 800 60"
            className="mt-6 w-full text-border-strong"
            role="img"
            aria-label="Browser to FastAPI to Sarvam, Qdrant and Gemini"
          >
            <line x1="60" y1="30" x2="740" y2="30" stroke="currentColor" strokeDasharray="4 6" />
            {["Browser", "FastAPI", "Sarvam / Qdrant / LLM"].map((label, i) => (
              <g key={label} transform={`translate(${60 + i * 340}, 30)`}>
                <circle r="5" fill="currentColor" />
                <text
                  y="-14"
                  fill="currentColor"
                  fontSize="11"
                  fontFamily="IBM Plex Mono, monospace"
                  textAnchor={i === 0 ? "start" : i === 2 ? "end" : "middle"}
                >
                  {label}
                </text>
              </g>
            ))}
          </svg>
        </section>

        <div className="mt-14 grid gap-x-12 gap-y-10 md:grid-cols-2">
          {SECTIONS.map((s) => (
            <section key={s.n} className="border-t border-border pt-5">
              <h2 className="font-mono text-[0.6875rem] tracking-[0.18em] uppercase">
                <span className="text-primary">{s.n}</span> — {s.title}
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-foreground/80">{s.body}</p>
            </section>
          ))}
        </div>
      </main>
    </div>
  );
}
