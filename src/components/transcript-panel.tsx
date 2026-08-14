import { CopyButton } from "@/components/copy-button";

export function TranscriptPanel({ transcript }: { transcript: string }) {
  if (!transcript) return null;
  return (
    <section aria-labelledby="transcript-heading" className="border-t border-border py-6">
      <div className="flex items-center justify-between gap-4">
        <h2 id="transcript-heading" className="label-mono">
          You asked
        </h2>
        <CopyButton value={transcript} label="Copy transcript" />
      </div>
      <p className="mt-3 font-display text-2xl leading-snug text-foreground">
        “{transcript}”
      </p>
    </section>
  );
}
