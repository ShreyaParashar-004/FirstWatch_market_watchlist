import { ChevronRight } from "lucide-react";
import type { ReactNode } from "react";

export function Disclosure({
  summary,
  children,
  defaultOpen = false,
}: {
  summary: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  return (
    <details className="group border-t border-border pt-4" open={defaultOpen}>
      <summary className="flex cursor-pointer list-none items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground [&::-webkit-details-marker]:hidden">
        <ChevronRight className="h-3.5 w-3.5 shrink-0 transition-transform duration-150 group-open:rotate-90" />
        {summary}
      </summary>
      <div className="mt-4">{children}</div>
    </details>
  );
}