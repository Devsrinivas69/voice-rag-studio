import {
  RagApiError,
  ragResponseSchema,
  type LanguageCode,
  type RagResponse,
} from "@/types/api";
import { extensionForMime } from "@/lib/audio";
import { demoResponse } from "@/lib/demo";

export const API_BASE_URL: string =
  (import.meta.env["VITE_API_URL"] as string | undefined) ?? "http://localhost:8000";

export const DEMO_MODE: boolean =
  (import.meta.env["VITE_DEMO_MODE"] as string | undefined) === "true";

const REQUEST_TIMEOUT_MS = 45_000;

async function request(path: string, init: RequestInit, timeout = REQUEST_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(`${API_BASE_URL}${path}`, { ...init, signal: controller.signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new RagApiError("TIMEOUT");
    }
    throw new RagApiError("OFFLINE");
  } finally {
    clearTimeout(timer);
  }
}

async function parse(res: Response): Promise<RagResponse> {
  if (res.status === 401 || res.status === 403) throw new RagApiError("OFFLINE");
  if (res.status >= 500) throw new RagApiError("OFFLINE");
  let json: unknown;
  try {
    json = await res.json();
  } catch {
    throw new RagApiError("INVALID_RESPONSE");
  }
  const parsed = ragResponseSchema.safeParse(json);
  if (!parsed.success) throw new RagApiError("INVALID_RESPONSE");
  return parsed.data;
}

export const ragApi = {
  async voiceQuery(audio: Blob, language: LanguageCode): Promise<RagResponse> {
    if (DEMO_MODE) return demoResponse(language, undefined);
    if (audio.size === 0) throw new RagApiError("EMPTY_AUDIO");
    const form = new FormData();
    form.append("audio", audio, `question.${extensionForMime(audio.type)}`);
    form.append("language", language);
    const res = await request("/api/voice/query", { method: "POST", body: form });
    return parse(res);
  },

  async textQuery(query: string, language: LanguageCode): Promise<RagResponse> {
    if (DEMO_MODE) return demoResponse(language, query);
    const res = await request("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, language }),
    });
    return parse(res);
  },

  async healthCheck(): Promise<boolean> {
    if (DEMO_MODE) return true;
    try {
      const res = await request("/health", { method: "GET" }, 6000);
      return res.ok;
    } catch {
      return false;
    }
  },
};
