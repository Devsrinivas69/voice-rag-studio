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
  id: z.string(),
  text: z.string(),
  score: z.number().optional(),
  language: z.string().optional(),
  strategy: z.string().optional(),
  metadata: z.record(z.union([z.string(), z.number(), z.boolean()])).optional(),
});
export type Source = z.infer<typeof sourceSchema>;

export const latencySchema = z.object({
  stt: z.number().optional(),
  embedding: z.number().optional(),
  dense_retrieval: z.number().optional(),
  bm25: z.number().optional(),
  fusion: z.number().optional(),
  rerank: z.number().optional(),
  llm: z.number().optional(),
  grounding: z.number().optional(),
  total: z.number().optional(),
});
export type LatencyMetrics = z.infer<typeof latencySchema>;

export const errorResponseSchema = z.object({
  code: z.string().optional(),
  message: z.string().optional(),
});
export type ErrorResponse = z.infer<typeof errorResponseSchema>;

export const ragResponseSchema = z.object({
  success: z.boolean(),
  transcript: z.string().default(""),
  answer: z.string().default(""),
  grounded: z.boolean().default(false),
  confidence: z.number().optional(),
  should_answer: z.boolean().default(true),
  blocked: z.boolean().optional(),
  sources: z.array(sourceSchema).default([]),
  latency: latencySchema.default({}),
  request_id: z.string().default(""),
  error: errorResponseSchema.optional(),
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
