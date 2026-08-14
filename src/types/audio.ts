export type RecorderState =
  | "IDLE"
  | "REQUESTING_PERMISSION"
  | "RECORDING"
  | "STOPPING"
  | "UPLOADING"
  | "TRANSCRIBING"
  | "RETRIEVING"
  | "GENERATING"
  | "VERIFYING"
  | "SUCCESS"
  | "ERROR";

export const PROCESSING_STATES: RecorderState[] = [
  "UPLOADING",
  "TRANSCRIBING",
  "RETRIEVING",
  "GENERATING",
  "VERIFYING",
];

export const STATE_LABELS: Record<RecorderState, string> = {
  IDLE: "Tap to speak",
  REQUESTING_PERMISSION: "Requesting microphone…",
  RECORDING: "Listening…",
  STOPPING: "Finishing recording…",
  UPLOADING: "Uploading audio…",
  TRANSCRIBING: "Transcribing voice…",
  RETRIEVING: "Searching the dataset…",
  GENERATING: "Generating response…",
  VERIFYING: "Verifying answer…",
  SUCCESS: "Ask another question",
  ERROR: "Try again",
};

export const MAX_RECORDING_MS = 30_000;
export const MAX_AUDIO_BYTES = 10 * 1024 * 1024;
