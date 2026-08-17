import { z } from "zod";

export const LANGUAGES = [
  { label: "English", code: "en-IN" },
  { label: "Hindi", code: "hi-IN" },
  { label: "Kannada", code: "kn-IN" },
  { label: "Tamil", code: "ta-IN" },
  { label: "Telugu", code: "te-IN" },
  { label: "Malayalam", code: "ml-IN" },
  { label: "Marathi", code: "mr-IN" },
  { label: "Bengali", code: "bn-IN" },
  { label: "Gujarati", code: "gu-IN" },
] as const;

export type LanguageCode = (typeof LANGUAGES)[number]["code"];

export const sourceSchema = z.object({
  id: z.string().nullable().optional(),
  chunk_id: z.string().nullable().optional(),
  document_id: z.string().nullable().optional(),
  text: z.string().default(""),
  score: z.number().nullable().optional(),
  language: z.string().nullable().optional(),
  strategy: z.string().nullable().optional(),
  metadata: z.record(z.any()).nullable().optional(),
});
export type Source = z.infer<typeof sourceSchema>;

export const latencySchema = z.object({
  audio_validation_ms: z.number().nullable().optional(),
  stt: z.number().nullable().optional(),
  stt_ms: z.number().nullable().optional(),
  query_normalization_ms: z.number().nullable().optional(),
  routing_ms: z.number().nullable().optional(),
  embedding: z.number().nullable().optional(),
  embedding_ms: z.number().nullable().optional(),
  dense_retrieval: z.number().nullable().optional(),
  dense_retrieval_ms: z.number().nullable().optional(),
  bm25: z.number().nullable().optional(),
  bm25_ms: z.number().nullable().optional(),
  fusion: z.number().nullable().optional(),
  fusion_ms: z.number().nullable().optional(),
  rerank: z.number().nullable().optional(),
  reranking_ms: z.number().nullable().optional(),
  context_building_ms: z.number().nullable().optional(),
  llm: z.number().nullable().optional(),
  llm_ms: z.number().nullable().optional(),
  grounding: z.number().nullable().optional(),
  grounding_ms: z.number().nullable().optional(),
  total: z.number().nullable().optional(),
  total_backend_ms: z.number().nullable().optional(),
});
export type LatencyMetrics = z.infer<typeof latencySchema>;

export const errorResponseSchema = z.object({
  code: z.string().nullable().optional(),
  message: z.string().nullable().optional(),
});
export type ErrorResponse = z.infer<typeof errorResponseSchema>;

export const ragResponseSchema = z.object({
  success: z.boolean().default(true),
  request_id: z.string().default(""),
  transcript: z.string().nullable().optional(),
  answer: z.string().default(""),
  grounded: z.boolean().default(false),
  confidence: z.number().nullable().optional(),
  should_answer: z.boolean().default(true),
  blocked: z.boolean().nullable().optional(),
  sources: z.array(sourceSchema).default([]),
  latency: latencySchema.default({}),
  error: errorResponseSchema.nullable().optional(),
});
export type RagResponse = z.infer<typeof ragResponseSchema>;

export const healthSchema = z.object({
  status: z.string().optional(),
});

export interface VoiceQueryRequest {
  audio: Blob;
  language: LanguageCode;
}

export interface TextQueryRequest {
  query: string;
  language: LanguageCode;
}

export type ApiErrorCode =
  | "MIC_DENIED"
  | "UNSUPPORTED"
  | "OFFLINE"
  | "STT_FAILED"
  | "TIMEOUT"
  | "INVALID_RESPONSE"
  | "EMPTY_AUDIO"
  | "UNKNOWN";

export const ERROR_MESSAGES: Record<ApiErrorCode, string> = {
  MIC_DENIED: "Microphone access is required to ask a voice question.",
  UNSUPPORTED: "Voice recording isn't supported by this browser.",
  OFFLINE: "RAG service is currently unavailable.",
  STT_FAILED: "Speech transcription failed. Please try again.",
  TIMEOUT: "The request took too long to complete. Please try again.",
  INVALID_RESPONSE: "Received an invalid response from the RAG service.",
  EMPTY_AUDIO: "No audio was captured. Please try recording again.",
  UNKNOWN: "Something went wrong. Please try again.",
};

export class RagApiError extends Error {
  code: ApiErrorCode;
  constructor(code: ApiErrorCode, message?: string) {
    super(message ?? ERROR_MESSAGES[code]);
    this.code = code;
    this.name = "RagApiError";
  }
}
