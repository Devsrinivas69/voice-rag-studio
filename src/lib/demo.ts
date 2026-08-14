import type { LanguageCode, RagResponse } from "@/types/api";

const OFF_TOPIC = /weather|football|stock|movie|joke/i;

function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

/** Mocked backend response. Only ever used when VITE_DEMO_MODE === "true". */
export async function demoResponse(language: LanguageCode, query?: string): Promise<RagResponse> {
  await delay(1400);
  const transcript = query ?? "What does the dataset say about education access?";
  const offTopic = OFF_TOPIC.test(transcript);

  if (offTopic) {
    return {
      success: true,
      transcript,
      answer: "",
      grounded: false,
      should_answer: false,
      confidence: 0.12,
      sources: [],
      latency: { stt: 84, dense_retrieval: 31, bm25: 12, rerank: 18, total: 145 },
      request_id: "demo-8fa2c1",
    };
  }

  return {
    success: true,
    transcript,
    answer:
      "The dataset reports **steady gains in school enrolment** across surveyed districts, with the largest improvement in secondary education.\n\nKey points:\n- Enrolment rose from 71% to 84% over the review period.\n- Dropout rates remain highest between grades 8 and 10.\n- Digital learning access is unevenly distributed across rural blocks.",
    grounded: true,
    confidence: 0.91,
    should_answer: true,
    sources: [
      {
        id: "chunk_82af91",
        text: "Secondary school enrolment across the surveyed districts increased from 71 percent to 84 percent during the review period, with the sharpest gains recorded in coastal blocks.",
        score: 0.91,
        language,
        strategy: "Semantic chunk",
      },
      {
        id: "chunk_1d40be",
        text: "Dropout concentration remains between grades 8 and 10, driven primarily by seasonal migration and transport availability.",
        score: 0.87,
        language,
        strategy: "Sentence window",
      },
      {
        id: "chunk_77c3aa",
        text: "Digital learning access is reported as uneven, with rural blocks averaging 2.3 shared devices per classroom.",
        score: 0.82,
        language,
        strategy: "Metadata chunk",
      },
    ],
    latency: {
      stt: 84,
      embedding: 9,
      dense_retrieval: 31,
      bm25: 12,
      fusion: 4,
      rerank: 18,
      llm: 96,
      grounding: 21,
      total: 275,
    },
    request_id: "demo-8fa2c1",
  };
}
