import { Fragment, type ReactNode } from "react";

/** Minimal, safe markdown renderer: no HTML is ever injected. */
function inline(text: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
  return parts.filter(Boolean).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded-xs bg-muted px-1 py-0.5 font-mono text-[0.85em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function MarkdownText({ text }: { text: string }) {
  const blocks = text.split(/\n{2,}/);
  return (
    <div className="space-y-4">
      {blocks.map((block, bi) => {
        const lines = block.split("\n");
        const isList = lines.every((l) => /^\s*[-*]\s+/.test(l));
        if (isList) {
          return (
            <ul key={bi} className="space-y-2 pl-4">
              {lines.map((l, li) => (
                <li
                  key={li}
                  className="list-disc text-[0.975rem] leading-relaxed marker:text-primary"
                >
                  {inline(l.replace(/^\s*[-*]\s+/, ""))}
                </li>
              ))}
            </ul>
          );
        }
        if (/^#{1,3}\s/.test(block)) {
          return (
            <h4 key={bi} className="font-mono text-sm tracking-wide text-foreground">
              {inline(block.replace(/^#{1,3}\s/, ""))}
            </h4>
          );
        }
        return (
          <p key={bi} className="text-[1.0625rem] leading-[1.75] text-foreground/90">
            {inline(block)}
          </p>
        );
      })}
    </div>
  );
}
