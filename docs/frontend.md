# HHGOA Voice RAG — Frontend

Voice-enabled multilingual RAG client. The frontend is a pure HTTP client for an external
FastAPI backend; no retrieval, STT, embedding or LLM logic runs here.

> Stack note: this project runs on **TanStack Start (React 19 + TypeScript + Tailwind v4 + Vite)**
> rather than Next.js. Environment variables therefore use the `VITE_` prefix instead of
> `NEXT_PUBLIC_`. Everything else follows the original specification.

## Architecture

```
Browser (this app)
   ↓ multipart / JSON over HTTPS
FastAPI
   ↓
Sarvam STT · Qdrant · BM25 · LLM
```

## Components

| Path                                                   | Purpose                                                 |
| ------------------------------------------------------ | ------------------------------------------------------- |
| `src/components/header.tsx`                            | Branding, nav, health status, demo badge                |
| `src/components/voice-recorder.tsx`                    | Mic control + state label + duration                    |
| `src/components/waveform.tsx`                          | Live waveform from real mic amplitude                   |
| `src/components/language-selector.tsx`                 | 9 Indic language codes                                  |
| `src/components/transcript-panel.tsx`                  | "You asked" + copy                                      |
| `src/components/answer-panel.tsx`                      | Focal answer, grounding, confidence                     |
| `src/components/source-card.tsx` / `sources-panel.tsx` | Retrieved evidence, expand/collapse                     |
| `src/components/grounding-badge.tsx`                   | Grounded / not grounded (icon + text, not colour alone) |
| `src/components/latency-panel.tsx`                     | Measured metrics, `—` when missing                      |
| `src/components/pipeline-status.tsx`                   | Stage states: idle / processing / complete / error      |
| `src/components/request-id.tsx`                        | Debug reference + copy                                  |
| `src/components/example-prompts.tsx`                   | Empty state; fills the text fallback only               |
| `src/components/error-state.tsx`                       | Error, guardrail and no-evidence states                 |
| `src/components/text-fallback.tsx`                     | Typed query path                                        |

Hooks: `src/hooks/use-voice-recorder.ts`, `src/hooks/use-rag-query.ts`.
Lib: `src/lib/api.ts`, `src/lib/audio.ts`, `src/lib/demo.ts`.
Types: `src/types/api.ts`, `src/types/audio.ts`.

## Recording flow

1. Feature detection (`MediaRecorder` + `getUserMedia`).
2. Permission request; denial maps to a friendly message.
3. MIME negotiation: `audio/webm;codecs=opus` → `audio/webm` → `audio/ogg;codecs=opus` → `audio/mp4`.
4. Web Audio `AnalyserNode` drives the waveform from real amplitude; failure degrades to a static indicator.
5. Hard cap of 30s; duplicate submissions blocked by an in-flight guard.
6. On stop, all tracks and the `AudioContext` are torn down. Audio is never persisted or logged.

## API communication

Single client (`ragApi`) centralises base URL, timeouts (45s via `AbortController`), error
mapping and Zod response validation.

- `POST /api/voice/query` — `multipart/form-data` with `audio`, `language`
- `POST /api/query` — `{ query, language }`
- `GET /health` — checked once on mount, no aggressive polling

Malformed payloads surface "Received an invalid response from the RAG service." rather than crashing.

## Environment variables

| Variable         | Meaning                                               |
| ---------------- | ----------------------------------------------------- |
| `VITE_API_URL`   | FastAPI base URL, e.g. `http://localhost:8000`        |
| `VITE_DEMO_MODE` | `true` serves mocked responses; badge shown in header |

No provider secrets ever live in the frontend.

## Local development

```bash
cp .env.example .env.local
npm install
npm run dev
```

## Microphone permissions

Browsers only grant `getUserMedia` on `https://` or `http://localhost`. If the user blocks the
prompt, the permission must be reset from the browser site settings; the UI explains this and the
text fallback remains fully usable.

## Demo mode

Set `VITE_DEMO_MODE=true` to develop without a backend. Demo data lives solely in `src/lib/demo.ts`
and is unreachable when the flag is false.

## Deployment

Static build (`npm run build`) plus a `VITE_API_URL` pointing at the deployed FastAPI service.
CORS must allow the frontend origin.
