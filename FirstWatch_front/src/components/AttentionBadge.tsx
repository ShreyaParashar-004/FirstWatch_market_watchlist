import { attentionLabel, type AttentionLevel } from "@/lib/format";
import { cn } from "@/lib/utils";

const styles: Record<AttentionLevel, string> = {
  normal: "text-muted-foreground border-border",
  worth_watching: "text-attention-watch border-attention-watch/40",
  meaningful: "text-attention-meaningful border-attention-meaningful/50",
  high: "text-attention-high border-attention-high/60",
};

export function AttentionBadge({ level }: { level: AttentionLevel }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2.5 py-0.5 text-xs font-medium",
        // "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium",
        styles[level],
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {attentionLabel[level]}
    </span>
  );
}
