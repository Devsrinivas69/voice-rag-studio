import { AlertTriangle, Check } from "lucide-react";

export function GroundingBadge({ grounded }: { grounded: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-xs border px-2.5 py-1 font-mono text-[0.6875rem] tracking-[0.16em] uppercase ${
        grounded
          ? "border-success/50 text-success"
          : "border-warning/50 text-warning"
      }`}
    >
      {grounded ? (
        <Check className="size-3.5" aria-hidden="true" />
      ) : (
        <AlertTriangle className="size-3.5" aria-hidden="true" />
      )}
      {grounded ? "Grounded" : "Not grounded"}
    </span>
  );
}

export function GroundingNote({ grounded }: { grounded: boolean }) {
  return (
    <p className="text-sm text-muted-foreground">
      {grounded
        ? "✓ Answer supported by retrieved context"
        : "! Answer could not be verified against retrieved context"}
    </p>
  );
}
