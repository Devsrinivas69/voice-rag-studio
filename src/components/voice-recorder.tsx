import { Mic, Square, X } from "lucide-react";
import { Waveform } from "@/components/waveform";
import { formatDuration } from "@/lib/audio";
import { MAX_RECORDING_MS, STATE_LABELS, type RecorderState } from "@/types/audio";

interface Props {
  state: RecorderState;
  isRecording: boolean;
  elapsedMs: number;
  levels: number[];
  supported: boolean;
  onStart: () => void;
  onStop: () => void;
  onCancel: () => void;
  onReset: () => void;
}

export function VoiceRecorder({
  state,
  isRecording,
  elapsedMs,
  levels,
  supported,
  onStart,
  onStop,
  onCancel,
  onReset,
}: Props) {
  const busy = !["IDLE", "RECORDING", "SUCCESS", "ERROR"].includes(state);
  const label = isRecording ? "Listening…" : STATE_LABELS[state];

  const handleClick = () => {
    if (isRecording) return onStop();
    if (state === "SUCCESS" || state === "ERROR") onReset();
    void onStart();
  };

  return (
    <div className="flex flex-col items-center gap-5">
      <div className="relative">
        {isRecording && (
          <span
            aria-hidden="true"
            className="pulse-ring absolute inset-0 rounded-full border border-primary/40"
          />
        )}
        <button
          type="button"
          onClick={handleClick}
          disabled={busy || !supported}
          aria-label={isRecording ? "Stop voice recording" : "Start voice recording"}
          aria-pressed={isRecording}
          className={`relative flex size-24 items-center justify-center rounded-full border transition-all duration-200 disabled:cursor-not-allowed disabled:opacity-50 ${
            isRecording
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border-strong bg-surface text-foreground hover:border-primary hover:scale-[1.02]"
          }`}
        >
          {isRecording ? (
            <Square className="size-7 fill-current" aria-hidden="true" />
          ) : (
            <Mic className="size-8" aria-hidden="true" />
          )}
        </button>
      </div>

      <div className="flex min-h-[3.5rem] flex-col items-center gap-2">
        {isRecording ? (
          <>
            <Waveform levels={levels} />
            <p className="label-mono">
              {formatDuration(elapsedMs)} / {formatDuration(MAX_RECORDING_MS)}
            </p>
          </>
        ) : (
          <p className="label-mono text-foreground">
            {supported ? label : "Voice unsupported — use text"}
          </p>
        )}
      </div>

      {isRecording && (
        <button
          type="button"
          onClick={onCancel}
          className="label-mono inline-flex items-center gap-1.5 hover:text-foreground"
        >
          <X className="size-3" aria-hidden="true" /> Cancel
        </button>
      )}
    </div>
  );
}
