import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { CopyButton } from "@/components/copy-button";
import type { Source } from "@/types/api";

interface Props extends Source {
  index: number;
}

export function SourceCard({ index, id, text, score, language, strategy, metadata }: Props) {
  const [open, setOpen] = useState(false);
  const excerpt = text.length > 140 ? `${text.slice(0, 140)}…` : text;

  return (
    <article className="border border-border bg-card/60">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-border px-4 py-2.5">
        <span className="font-mono text-[0.6875rem] tracking-[0.16em] text-primary uppercase">
          Source {String(index + 1).padStart(2, "0")}
        </span>
        <span className="font-mono text-[0.6875rem] text-muted-foreground">{id}</span>
        {strategy && <span className="label-mono">{strategy}</span>}
        {language && <span className="label-mono">{language}</span>}
        {typeof score === "number" && (
          <span className="ml-auto font-mono text-[0.6875rem] text-foreground">
            Score {score.toFixed(2)}
          </span>
        )}
      </div>

      <div className="px-4 py-3">
        <p className="text-sm leading-relaxed text-foreground/85">{open ? text : excerpt}</p>

        {open && metadata && Object.keys(metadata).length > 0 && (
          <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 border-t border-border pt-3">
            {Object.entries(metadata).map(([k, v]) => (
              <div key={k} className="contents">
                <dt className="label-mono">{k}</dt>
                <dd className="font-mono text-xs text-foreground/80">{String(v)}</dd>
              </div>
            ))}
          </dl>
        )}

        <div className="mt-3 flex items-center gap-2">
          <button
            type="button"
            onClick={() => setOpen((o) => !o)}
            aria-expanded={open}
            className="label-mono inline-flex items-center gap-1.5 rounded-xs border border-border px-2 py-1 hover:border-border-strong hover:text-foreground"
          >
            <ChevronDown
              className={`size-3 transition-transform ${open ? "rotate-180" : ""}`}
              aria-hidden="true"
            />
            {open ? "Hide evidence" : "View evidence"}
          </button>
          <CopyButton value={text} label={`Copy source ${index + 1}`} />
        </div>
      </div>
    </article>
  );
}
