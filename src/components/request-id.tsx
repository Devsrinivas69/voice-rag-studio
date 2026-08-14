import { CopyButton } from "@/components/copy-button";

export function RequestId({ id }: { id: string }) {
  if (!id) return null;
  return (
    <div className="flex items-center gap-3 border-t border-border py-4">
      <span className="label-mono">Request</span>
      <code className="font-mono text-xs text-foreground/80">#{id}</code>
      <CopyButton value={id} label="Copy request id" />
    </div>
  );
}
