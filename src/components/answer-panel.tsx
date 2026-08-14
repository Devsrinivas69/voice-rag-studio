import { CopyButton } from "@/components/copy-button";
import { GroundingBadge, GroundingNote } from "@/components/grounding-badge";
import { MarkdownText } from "@/components/markdown-text";
import type { RagResponse } from "@/types/api";

export function AnswerPanel({ result }: { result: RagResponse }) {
  return (
    <section aria-labelledby="answer-heading" className="border-t border-border py-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="answer-heading" className="label-mono">
          Answer
        </h2>
        <div className="flex items-center gap-2">
          <GroundingBadge grounded={result.grounded} />
          <CopyButton value={result.answer} label="Copy answer" />
        </div>
      </div>

      <div className="mt-5">
        <MarkdownText text={result.answer} />
      </div>

      <div className="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-border pt-4">
        <GroundingNote grounded={result.grounded} />
        {typeof result.confidence === "number" && (
          <span className="label-mono">Confidence {(result.confidence * 100).toFixed(0)}%</span>
        )}
        <span className="label-mono">{result.sources.length} sources</span>
      </div>
    </section>
  );
}
