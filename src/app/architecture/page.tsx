import type { Metadata } from "next";
import { ArchitectureView } from "./architecture-view";

export const metadata: Metadata = {
  title: "Architecture — HHGOA Voice RAG",
  description:
    "How the HHGOA Voice RAG pipeline works: Sarvam STT, hybrid BM25 + vector retrieval, RRF fusion, reranking, generation and grounding verification.",
  openGraph: {
    title: "Architecture — HHGOA Voice RAG",
    description:
      "Voice to grounded answer: STT, hybrid retrieval, RRF, reranking, generation, grounding.",
    type: "article",
  },
  twitter: {
    card: "summary_large_image",
  },
};

export default function ArchitecturePage() {
  return <ArchitectureView />;
}
