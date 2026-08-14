import { SendHorizonal } from "lucide-react";
import type { FormEvent } from "react";

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled: boolean;
}

export function TextFallback({ value, onChange, onSubmit, disabled }: Props) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="mt-8 border-t border-border pt-6">
      <label htmlFor="text-query" className="label-mono">
        Prefer typing?
      </label>
      <div className="mt-3 flex gap-2">
        <input
          id="text-query"
          type="text"
          value={value}
          maxLength={500}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Type your question about the dataset…"
          className="min-w-0 flex-1 border border-border bg-surface px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="inline-flex items-center gap-2 border border-border-strong bg-surface px-4 py-2.5 font-mono text-[0.6875rem] tracking-[0.16em] uppercase transition-colors hover:border-primary disabled:opacity-40"
        >
          <SendHorizonal className="size-3.5" aria-hidden="true" />
          Ask
        </button>
      </div>
    </form>
  );
}
