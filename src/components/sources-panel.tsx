import { SourceCard } from "@/components/source-card";
import type { Source } from "@/types/api";

export function SourcesPanel({ sources }: { sources: Source[] }) {
  if (sources.length === 0) return null;
  return (
    <section aria-labelledby="evidence-heading" className="border-t border-border py-6">
      <div className="flex items-center justify-between">
        <h2 id="evidence-heading" className="label-mono">
          Retrieved Evidence & Grounding Chunks
        </h2>
        <span className="label-mono">{sources.length} chunks</span>
      </div>
      <div className="mt-4 space-y-3">
        {sources.map((s, i) => {
          const keyId = s.chunk_id || s.id || `source_${i}`;
          return <SourceCard key={`${keyId}_${i}`} index={i} id={keyId} {...s} />;
        })}
      </div>
    </section>
  );
}
