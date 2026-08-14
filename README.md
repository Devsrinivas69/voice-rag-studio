# Voice RAG Studio

You are a senior frontend architect and product designer with 15+ years of experience building production-grade AI applications.

Build ONLY the frontend for my HHGOA Goa 2026 Task 2 project.

Do not implement backend logic, RAG, embeddings, Qdrant, BM25, Gemini, or Sarvam server-side integrations.

The frontend must communicate with an existing FastAPI backend through HTTP APIs.

The product is:

"HHGOA Voice RAG"

It is a voice-enabled multilingual Retrieval-Augmented Generation interface.

The user speaks a question.

The browser records audio.

The frontend sends the audio to FastAPI.

FastAPI handles Sarvam STT → retrieval → RAG → guardrails → response.

The frontend displays the transcript, answer, sources, grounding status, and latency.

==================================================

1. TECHNOLOGY

==================================================

Use:

- Next.js

- App Router

- React

- TypeScript

- Tailwind CSS

- Lucide React icons

Use modern React patterns.

Use strict TypeScript.

Do not use JavaScript.

Do not introduce unnecessary UI frameworks.

Do not use a backend inside Next.js.

Do not expose API secrets.

==================================================

2. DESIGN DIRECTION

==================================================

Create a premium technical AI-research interface.

Visual direction:

- dark-first

- minimal

- sophisticated

- high contrast

- technical

- editorial

- futuristic but not gimmicky

- generous whitespace

- subtle borders

- restrained animations

- excellent typography

Avoid:

- generic SaaS dashboard appearance

- excessive gradients

- excessive glassmorphism

- neon cyberpunk styling

- huge decorative illustrations

- unnecessary cards everywhere

- excessive animations

- fake AI visualizations

The interface should look like a serious AI engineering/research product.

Think:

AI laboratory + developer tool + premium editorial interface.

==================================================

3. BRANDING

==================================================

Primary product name:

HHGOA Voice RAG

Small eyebrow:

HACKER HOUSE GOA 2026

Task label:

TASK 02 / VOICE-ENABLED RAG

Use the following conceptual tagline:

"Speak. Retrieve. Verify."

Do not make the interface look like an official Hacker House Goa website.

Clearly present this as an independent project/demo.

==================================================

4. MAIN PAGE

==================================================

Create:

/

The main page should have the following structure:

--------------------------------

HEADER

--------------------------------

Left:

HHGOA

Voice RAG

Right:

TASK 02

STATUS: ONLINE

Optional GitHub icon/button.

--------------------------------

HERO

--------------------------------

Small eyebrow:

VOICE-ENABLED RETRIEVAL AUGMENTED GENERATION

Large heading:

"Ask the dataset."

Secondary text:

"Speak naturally. Retrieve relevant evidence. Get a grounded answer."

Then the primary interaction area.

--------------------------------

VOICE INTERACTION

--------------------------------

Large central microphone control.

Before recording:

"Tap to speak"

During recording:

"Listening..."

After recording:

"Processing..."

When completed:

"Ask another question"

Use a premium circular microphone interface.

Do not make it excessively large.

Add a subtle audio waveform while recording.

The waveform must represent actual microphone activity if possible.

Do not fake audio data.

--------------------------------

LANGUAGE

--------------------------------

Add a compact language selector.

Options:

English

Hindi

Kannada

Tamil

Telugu

Malayalam

Marathi

Bengali

Gujarati

Backend language codes:

en-IN

hi-IN

kn-IN

ta-IN

te-IN

ml-IN

mr-IN

bn-IN

gu-IN

Default:

English

--------------------------------

TRANSCRIPT

--------------------------------

After recording:

SHOW:

YOU ASKED

"[transcribed question]"

Allow copy-to-clipboard.

Do not allow editing unless explicitly useful.

--------------------------------

ANSWER

--------------------------------

Display:

ANSWER

Then the generated answer.

The answer should be the visual focal point.

Support markdown-style text safely.

Do not render arbitrary HTML.

--------------------------------

SOURCE EVIDENCE

--------------------------------

Show:

RETRIEVED EVIDENCE

Each source should display:

- source/chunk ID

- language

- retrieval score if available

- chunking strategy if available

- short excerpt

Example:

SOURCE 01

chunk_82af91

Semantic chunk

Score 0.91

"Relevant passage excerpt..."

Allow expand/collapse.

Do not display the entire dataset document by default.

--------------------------------

GROUNDING

--------------------------------

Show a clear status:

GROUNDED

or

NOT GROUNDED

If grounded:

✓ Answer supported by retrieved context

If not grounded:

! Answer could not be verified against retrieved context

Use accessible status indicators.

Do not use color alone to communicate state.

--------------------------------

LATENCY

--------------------------------

Display a compact technical metrics section.

Example:

PIPELINE

STT       84 ms

RETRIEVAL 31 ms

RERANK    18 ms

LLM       96 ms

TOTAL     229 ms

These values must come from the backend.

Never generate fake latency numbers.

If a metric is unavailable, show:

—

==================================================

5. TECHNICAL PIPELINE VISUALIZATION

==================================================

Create a small horizontal/vertical pipeline visualization.

Show:

VOICE

 ↓

STT

 ↓

QUERY

 ↓

HYBRID RETRIEVAL

 ↓

RERANK

 ↓

GENERATE

 ↓

VERIFY

Each stage should have a status:

idle

processing

complete

error

During processing, animate only the active stage.

Do not animate every element continuously.

The visualization should help judges understand the architecture immediately.

==================================================

6. BACKEND API

==================================================

Create a centralized API client.

Example:

lib/api.ts

Backend URL must come from:

NEXT_PUBLIC_API_URL

Example:

NEXT_PUBLIC_API_URL=http://localhost:8000

This is NOT a secret.

Never put:

SARVAM_API_KEY

GEMINI_API_KEY

QDRANT_API_KEY

in frontend environment variables.

The browser communicates only with FastAPI.

Architecture:

Browser

 ↓

Next.js

 ↓

FastAPI

 ↓

Sarvam / Qdrant / Gemini

==================================================

7. ENVIRONMENT FILE

==================================================

Create:

.env.example

with:

NEXT_PUBLIC_API_URL=http://localhost:8000

Do not create real secrets.

Document:

1. Copy .env.example to .env.local

2. Set NEXT_PUBLIC_API_URL

3. Start FastAPI

4. Start Next.js

==================================================

8. API TYPES

==================================================

Create strongly typed TypeScript interfaces.

Example request:

VoiceQueryRequest

Fields:

audio

language

Backend response should support:

{

  success: boolean,

  transcript: string,

  answer: string,

  grounded: boolean,

  confidence?: number,

  should_answer: boolean,

  sources: Source[],

  latency: LatencyMetrics,

  request_id: string,

  error?: ErrorResponse

}

Create:

types/api.ts

Do not use:

any

unless absolutely unavoidable.

==================================================

9. VOICE RECORDING

==================================================

Use the browser MediaRecorder API.

Requirements:

- request microphone permission

- detect unsupported browser

- start recording

- stop recording

- cancel recording

- prevent duplicate submissions

- handle microphone permission denial

- handle recording errors

- handle empty audio

- show recording duration

- maximum duration

- cleanup MediaRecorder streams

Prefer WebM audio where supported.

Detect the browser's supported MIME type rather than blindly assuming one.

Example logic:

audio/webm;codecs=opus

fallback:

audio/webm

fallback:

audio/mp4

depending on browser support.

Do not hardcode a format that may not work.

==================================================

10. RECORDING STATES

==================================================

Create a state machine.

States:

IDLE

REQUESTING_PERMISSION

RECORDING

STOPPING

UPLOADING

TRANSCRIBING

RETRIEVING

GENERATING

VERIFYING

SUCCESS

ERROR

The UI must reflect these states.

Do not use multiple unrelated booleans such as:

isRecording

isLoading

isProcessing

isError

if a state machine can represent the state more reliably.

==================================================

11. AUDIO WAVEFORM

==================================================

During recording:

display a subtle live waveform.

Use Web Audio API where practical.

The waveform should respond to actual microphone input.

Do not use a fake looping animation pretending to represent audio.

If microphone analysis is unavailable, gracefully fall back to a subtle recording indicator.

==================================================

12. API REQUEST

==================================================

Send:

POST /api/voice/query

Use:

multipart/form-data

Fields:

audio

language

Use AbortController.

Implement a reasonable client timeout.

Do not retry blindly.

If the backend returns a retryable error, show a useful message.

==================================================

13. ERROR UX

==================================================

Create professional error states.

Examples:

Microphone denied:

"Microphone access is required to ask a voice question."

Unsupported browser:

"Voice recording isn't supported by this browser."

Backend unavailable:

"RAG service is currently unavailable."

STT failure:

"Speech transcription failed. Please try again."

No relevant evidence:

"No reliable answer was found in the provided dataset."

Timeout:

"The request took too long to complete. Please try again."

Do not display raw backend stack traces.

Do not expose internal errors.

==================================================

14. OFF-TOPIC RESPONSE

==================================================

The backend may return:

should_answer=false

The frontend must distinguish this from a system failure.

Example UI:

NOT ENOUGH EVIDENCE

"I couldn't find enough relevant information in the provided dataset to answer that reliably."

Do not show:

ERROR

because this is an intentional guardrail response.

==================================================

15. PROMPT INJECTION RESULT

==================================================

If backend returns a security/guardrail event:

Display:

REQUEST BLOCKED

"That request could not be processed safely."

Do not expose internal guardrail rules.

Do not reveal system prompts.

==================================================

16. SOURCE COMPONENT

==================================================

Create:

components/source-card.tsx

Props:

id

text

score

language

strategy

metadata

Design:

small technical card.

Show only a short excerpt initially.

Click:

"View evidence"

expands the source.

Add:

Copy source

button.

==================================================

17. ANSWER COMPONENT

==================================================

Create:

components/answer-panel.tsx

Features:

- readable typography

- copy answer

- grounded status

- confidence if available

- source count

- answer timestamp if useful

Do not add unnecessary social/share features.

==================================================

18. LATENCY COMPONENT

==================================================

Create:

components/latency-panel.tsx

Show:

STT

Embedding

Dense retrieval

BM25

Fusion

Reranking

LLM

Grounding

Total

Only display metrics returned by the API.

Support missing metrics.

Allow an expandable "Technical details" section.

==================================================

19. REQUEST ID

==================================================

Show a small technical reference:

REQUEST

#8FA2C1

using the actual request_id.

Add copy button.

This is useful for debugging.

==================================================

20. RESPONSIVE DESIGN

==================================================

Must work on:

Desktop

Laptop

Tablet

Mobile

Desktop:

two-column result layout where appropriate.

Mobile:

single-column.

Microphone interaction must remain easy to use with one hand.

Do not create horizontal overflow.

==================================================

21. ACCESSIBILITY

==================================================

Implement:

semantic HTML

ARIA labels

keyboard navigation

visible focus states

screen-reader-friendly status updates

sufficient contrast

reduced-motion support

Microphone button must have:

aria-label="Start voice recording"

during recording:

aria-label="Stop voice recording"

Use aria-live for processing/result status.

==================================================

22. ANIMATIONS

==================================================

Use subtle animations.

Allowed:

fade

slide

scale

pulse

waveform

Do not animate large amounts of text.

Respect:

prefers-reduced-motion

When reduced motion is enabled:

remove waveform animation

remove stage transitions

keep state changes instantaneous.

==================================================

23. NAVIGATION

==================================================

Keep navigation minimal.

Header:

HHGOA Voice RAG

Links:

Demo

Architecture

GitHub

If Architecture is implemented, create:

/architecture

Show a visual explanation of:

Voice

 ↓

Sarvam STT

 ↓

Query

 ↓

BM25 + Vector Search

 ↓

RRF

 ↓

Reranking

 ↓

LLM

 ↓

Grounding

This page is informational only.

Do not implement backend functionality here.

==================================================

24. ARCHITECTURE PAGE

==================================================

Create a polished technical architecture page.

Sections:

01 — Voice Input

02 — Speech Recognition

03 — Query Processing

04 — Hybrid Retrieval

05 — Reranking

06 — Generation

07 — Grounding

08 — Latency

For each:

Short explanation.

Keep text concise.

Include a system architecture diagram using HTML/CSS/SVG.

Do not generate a raster image for the architecture.

==================================================

25. EMPTY STATE

==================================================

Initial page should not look empty.

Show:

ASK THE DATASET

"Use your voice to ask a question."

Example prompts:

"What is discussed in this dataset about education?"

"What information is available about employment?"

"Ask a question in Kannada."

Clicking an example should NOT automatically send it.

It can optionally populate a text fallback input.

==================================================

26. TEXT FALLBACK

==================================================

Implement a text input as a fallback.

Reason:

Some browsers/devices may not support microphone recording.

Add:

"Prefer typing?"

Text input.

POST:

/api/query

Request:

{

  "query": "...",

  "language": "en-IN"

}

This is useful for testing the RAG system without repeatedly recording audio.

==================================================

27. DEMO MODE

==================================================

Create a frontend demo mode.

Environment:

NEXT_PUBLIC_DEMO_MODE=false

When true:

Use mocked backend responses.

This must make frontend development possible without API keys or a running backend.

Do not mix demo data into production mode.

Clearly display:

DEMO MODE

when enabled.

==================================================

28. LOADING EXPERIENCE

==================================================

Never show a generic:

"Loading..."

Instead show meaningful states:

Transcribing voice...

Searching the dataset...

Ranking evidence...

Generating response...

Verifying answer...

The frontend should display the actual pipeline stage if the backend provides it.

==================================================

29. SECURITY

==================================================

Frontend must:

- never contain API secrets

- never render unsanitized HTML

- never trust backend markdown blindly

- validate response shape

- limit audio upload

- avoid storing microphone recordings unnecessarily

- not persist voice recordings in localStorage

- not log audio blobs

- not log sensitive user content unnecessarily

==================================================

30. PERFORMANCE

==================================================

Optimize:

- initial bundle

- unnecessary re-renders

- component loading

- audio processing

- network requests

Do not add large UI libraries without justification.

Use dynamic imports only where they provide measurable value.

Do not over-engineer.

==================================================

31. COMPONENT STRUCTURE

==================================================

Use:

components/

    header.tsx

    voice-recorder.tsx

    waveform.tsx

    language-selector.tsx

    transcript-panel.tsx

    answer-panel.tsx

    source-card.tsx

    sources-panel.tsx

    grounding-badge.tsx

    latency-panel.tsx

    pipeline-status.tsx

    request-id.tsx

    example-prompts.tsx

    error-state.tsx

hooks/

    use-voice-recorder.ts

    use-rag-query.ts

lib/

    api.ts

    audio.ts

    utils.ts

types/

    api.ts

    audio.ts

==================================================

32. CODE QUALITY

==================================================

Use:

- clean component boundaries

- reusable hooks

- typed API clients

- error boundaries where appropriate

- no duplicated API logic

- no magic strings scattered through components

- no unnecessary global state

Prefer local state unless shared state is genuinely required.

==================================================

33. API CLIENT

==================================================

Create a single API abstraction.

Example:

ragApi.voiceQuery(...)

ragApi.textQuery(...)

ragApi.healthCheck(...)

Do not call fetch directly from multiple components.

Centralize:

base URL

headers

timeouts

error mapping

response validation

==================================================

34. RESPONSE VALIDATION

==================================================

Validate backend responses on the client.

Use Zod if appropriate.

If the backend returns malformed data:

show:

"Received an invalid response from the RAG service."

Do not crash the entire interface.

==================================================

35. HEALTH STATUS

==================================================

Header should optionally show:

SYSTEM ONLINE

or:

SYSTEM OFFLINE

Use:

GET /health

Do not continuously poll aggressively.

A manual retry option is acceptable.

==================================================

36. DEMO PRESENTATION MODE

==================================================

Add a clean presentation-friendly layout.

The judge should immediately understand:

1. What this is.

2. What to do.

3. What happened.

4. Where the answer came from.

5. Whether it is grounded.

6. How long it took.

Avoid making the judge search around the UI.

==================================================

37. VISUAL HIERARCHY

==================================================

Priority:

1. Voice interaction

2. Question

3. Answer

4. Evidence

5. Grounding

6. Latency

7. Technical metadata

Do not give technical metadata more visual weight than the answer.

==================================================

38. FINAL DEMO FLOW

==================================================

The finished frontend must support this exact demo:

OPEN APP

↓

Click microphone

↓

Speak question

↓

Show recording

↓

Stop

↓

Show:

"Transcribing..."

↓

Show transcript

↓

Show:

"Searching dataset..."

↓

Show retrieval pipeline

↓

Show answer

↓

Show retrieved evidence

↓

Show:

GROUNDED ✓

↓

Show latency

↓

Try an off-topic question

↓

Show:

NOT ENOUGH EVIDENCE

This flow must feel smooth and intentional.

==================================================

39. FRONTEND .ENV.EXAMPLE

==================================================

Create:

.env.example

containing only:

NEXT_PUBLIC_API_URL=http://localhost:8000

NEXT_PUBLIC_DEMO_MODE=false

Document:

cp .env.example .env.local

Then change:

NEXT_PUBLIC_API_URL=http://localhost:8000

No API secrets.

==================================================

40. DOCUMENTATION

==================================================

Create:

docs/frontend.md

Explain:

- architecture

- components

- recording flow

- API communication

- environment variables

- local development

- browser microphone permissions

- demo mode

- deployment

==================================================

41. TESTING

==================================================

Add tests for:

- microphone state transitions

- API error handling

- successful voice response

- off-topic response

- grounded response

- ungrounded response

- malformed API response

- language selection

- demo mode

Do not require a real microphone for automated tests.

Mock MediaRecorder.

Mock fetch/API calls.

==================================================

42. FINAL QUALITY CHECK

==================================================

Before completing:

Run:

npm install

npm run lint

npm run build

If tests exist:

npm test

Fix all TypeScript errors.

Fix all lint errors.

Fix all build errors.

Check:

desktop

mobile

keyboard navigation

microphone permission denial

backend offline

slow backend

empty response

invalid response

successful response

==================================================

43. IMPORTANT RESTRICTIONS

==================================================

Do NOT:

- implement backend RAG

- implement Qdrant

- implement BM25

- implement Gemini

- implement Sarvam API directly in browser

- expose API keys

- use NEXT_PUBLIC_SARVAM_API_KEY

- use NEXT_PUBLIC_GEMINI_API_KEY

- use NEXT_PUBLIC_QDRANT_API_KEY

- fabricate latency values

- fabricate source results

- fabricate confidence values

- hardcode production answers

- create fake AI processing in production mode

The frontend must be a real client for the FastAPI backend.

==================================================

44. EXECUTION STRATEGY

==================================================

Do not generate the entire frontend blindly.

First:

1. Inspect the repository.

2. Determine whether Next.js already exists.

3. Preserve existing working configuration where possible.

4. Identify the existing backend API contract.

5. If the API contract is missing, create TypeScript interfaces based on the specification above.

6. Implement the frontend incrementally.

Build in these stages:

STAGE 1:

Project setup

STAGE 2:

Design system

STAGE 3:

Main voice interface

STAGE 4:

MediaRecorder hook

STAGE 5:

API client

STAGE 6:

Results/evidence UI

STAGE 7:

Pipeline visualization

STAGE 8:

Error/guardrail states

STAGE 9:

Architecture page

STAGE 10:

Demo mode

STAGE 11:

Testing

STAGE 12:

Production optimization

After every stage:

- run lint

- run type checking

- verify build where appropriate

- report changed files

- report issues

Do not proceed by silently ignoring errors.

==================================================

45. FINAL ACCEPTANCE CRITERIA

==================================================

The frontend is complete only when:

[ ] Desktop UI works

[ ] Mobile UI works

[ ] Microphone recording works

[ ] MediaRecorder is handled safely

[ ] Audio is sent to FastAPI

[ ] Text fallback works

[ ] Language selector works

[ ] Transcript displays

[ ] Answer displays

[ ] Sources display

[ ] Grounding status displays

[ ] Latency displays

[ ] Pipeline status displays

[ ] Off-topic response displays correctly

[ ] Guardrail response displays correctly

[ ] Errors are handled professionally

[ ] API secrets are not exposed

[ ] Demo mode works

[ ] Architecture page works

[ ] Accessibility is implemented

[ ] Reduced-motion support exists

[ ] TypeScript has no errors

[ ] ESLint has no errors

[ ] Production build succeeds

[ ] Documentation exists

Start with STAGE 1 only.

Inspect the repository before changing anything.


┌─────────────────────────────────────────────────────────────┐

│ HHGOA VOICE RAG                 TASK 02       ● ONLINE      │

├─────────────────────────────────────────────────────────────┤

│                                                             │

│              HACKER HOUSE GOA 2026                          │

│                                                             │

│                  ASK THE DATASET.                           │

│        Speak naturally. Retrieve. Verify.                   │

│                                                             │

│                    ┌─────────┐                              │

│                    │   🎙    │                              │

│                    └─────────┘                              │

│                   TAP TO SPEAK                              │

│                                                             │

│                 Language: English                           │

│                                                             │

├─────────────────────────────────────────────────────────────┤

│ YOU ASKED                                                    │

│ "What does the dataset say about..."                        │

├─────────────────────────────────────────────────────────────┤

│ ANSWER                                    GROUNDED ✓         │

│                                                             │

│ Your generated grounded answer...                           │

│                                                             │

├─────────────────────────────────────────────────────────────┤

│ RETRIEVED EVIDENCE                                           │

│                                                             │

│ SOURCE 01       Semantic       Score 0.91                    │

│ SOURCE 02       Sentence      Score 0.87                    │

│ SOURCE 03       Metadata      Score 0.82                    │

├─────────────────────────────────────────────────────────────┤

│ PIPELINE                                                     │

│                                                             │

│ VOICE → STT → RETRIEVE → RERANK → GENERATE → VERIFY         │

│                                                             │

├─────────────────────────────────────────────────────────────┤

│ LATENCY                                                      │

│ STT       84ms     RETRIEVAL    31ms                        │

│ RERANK    18ms     LLM          96ms                        │

│ TOTAL     229ms                                             │

└─────────────────────────────────────────────────────────────┘


inspiration website: https://hhgoa.com/

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/d7b2e65b-9d87-43a5-8f9f-17564544ec12).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
