import { AlertTriangle, ShieldAlert, SearchX } from "lucide-react";

interface Props {
  title: string;
  message: string;
  variant?: "error" | "guardrail" | "no-evidence";
  onRetry?: () => void;
}

export function ErrorState({ title, message, variant = "error", onRetry }: Props) {
  const Icon =
    variant === "guardrail" ? ShieldAlert : variant === "no-evidence" ? SearchX : AlertTriangle;
  const tone =
    variant === "error"
      ? "border-destructive/40 text-destructive"
      : "border-warning/40 text-warning";

  return (
    <section role="alert" className={`mt-6 border ${tone} bg-card/50 p-5`}>
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <div>
          <h2 className="font-mono text-[0.6875rem] tracking-[0.18em] uppercase">{title}</h2>
          <p className="mt-2 text-sm text-foreground/85">{message}</p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="label-mono mt-4 rounded-xs border border-border px-2.5 py-1 text-foreground hover:border-border-strong"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
