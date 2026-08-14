const CANDIDATE_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/mp4",
];

export function isRecordingSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.MediaRecorder !== "undefined" &&
    !!navigator?.mediaDevices?.getUserMedia
  );
}

export function pickMimeType(): string | undefined {
  if (typeof window === "undefined" || typeof window.MediaRecorder === "undefined") {
    return undefined;
  }
  const isSupported = window.MediaRecorder.isTypeSupported;
  if (typeof isSupported !== "function") return undefined;
  return CANDIDATE_MIME_TYPES.find((type) => isSupported(type));
}

export function extensionForMime(mime: string | undefined): string {
  if (!mime) return "webm";
  if (mime.includes("mp4")) return "m4a";
  if (mime.includes("ogg")) return "ogg";
  return "webm";
}

export function formatDuration(ms: number): string {
  const total = Math.floor(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
