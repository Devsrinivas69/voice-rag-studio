import type { Metadata } from "next";
import { VoiceRagDemo } from "./voice-rag-demo";

export const metadata: Metadata = {
  title: "HHGOA Voice RAG — Speak. Retrieve. Verify.",
  description:
    "Voice-enabled multilingual retrieval augmented generation demo. Speak a question, retrieve evidence, and get a grounded, verifiable answer.",
  openGraph: {
    title: "HHGOA Voice RAG — Speak. Retrieve. Verify.",
    description:
      "Ask the dataset with your voice. Grounded answers with evidence and latency metrics.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
  },
};

export default function HomePage() {
  return <VoiceRagDemo />;
}
