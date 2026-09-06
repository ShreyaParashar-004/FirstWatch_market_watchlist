import { AttentionBadge } from "@/components/AttentionBadge";
import { Disclosure } from "@/components/Disclosure";
// import { attentionLevel, formatDate, formatDateTime, titleize } from "@/lib/format";
import { attentionLevel, formatDate, titleize } from "@/lib/format";
import type { Signal } from "@/lib/types";

// function Meta({ label, value }: { label: string; value: string | null }) {
//   if (!value) return null;
//   return (
//     <div>
//       <dt className="label-caps">{label}</dt>
//       <dd className="mt-1 text-sm text-foreground">{value}</dd>
//     </div>
//   );
// }


function directionClass(direction: string | null | undefined) {
  const d = (direction ?? "").toLowerCase();
  if (d === "positive") return "text-positive";
  if (d === "negative") return "text-negative";
  if (d === "uncertain") return "text-attention-meaningful";

  return "text-foreground";
}

function impactClass(impact: string | null | undefined) {
  const i = (impact ?? "").toLowerCase();
  if (i === "low") return "text-attention-watch";
  return "text-foreground";
}

function GlanceStat({
  label,
  value,
  className,
}: {
  label: string;
  value: string | null;
  className?: string;
}) {
  if (!value) return null;
  return (
    <div>
      <p className="label-caps">{label}</p>
      <p className={`mt-1 text-base font-semibold ${className ?? "text-foreground"}`}>{value}</p>
    </div>
  );
}

export function SignalCard({ signal }: { signal: Signal }) {
  const level = attentionLevel(signal);
  const confidence =
    typeof signal.confidence === "number" ? `${Math.round(signal.confidence * 100)}%` : null;
  const evidence = signal.evidence ?? [];
  // const entities = signal.affected_entities ?? [];
  const isEarly = (signal.signal_kind ?? "").toLowerCase() === "early";

  // const hasDetail =
  //   Boolean(signal.time_horizon) ||
  //   Boolean(signal.sentiment) ||
  //   Boolean(signal.source_agreement) ||
  //   Boolean(signal.first_evidence_at) ||
  //   Boolean(signal.latest_evidence_at) ||
  //   entities.length > 0;
  // const hasDetail = Boolean(signal.time_horizon);

  const showTimeHorizon =
    Boolean(signal.time_horizon) && (signal.time_horizon ?? "").toLowerCase() !== "uncertain";


  // Some evidence fields arrive as placeholder strings (e.g. "-") rather than
  // null when the backend has nothing to report. Treat those as absent too,
  // instead of rendering the placeholder as if it were real content.
  const hasText = (v: string | null | undefined) => Boolean(v && v.trim() && v.trim() !== "-");


  return (
    <article id={`signal-${signal.id}`} className="rounded-lg border border-border bg-card p-6">
      <div className="-mx-6 -mt-6 mb-5 flex flex-wrap items-center justify-between gap-3 rounded-t-lg border-b border-border bg-primary/[0.05] px-6 py-4">
        <div className="flex flex-wrap items-center gap-2">
          {signal.watch_label ? (
            // <span className="rounded-sm bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground">
            <span className="rounded-sm bg-secondary px-2.5 py-0.5 text-xs font-semibold text-primary">
              {signal.watch_label}
              {signal.watch_type ? (
                <span className="text-muted-foreground"> · {titleize(signal.watch_type)}</span>
              ) : null}
            </span>
          ) : null}
          {isEarly ? (
            <span className="rounded-sm border border-border px-2.5 py-0.5 text-xs text-muted-foreground">
              Early development
            </span>
          ) : null}
          {signal.market_already_moved ? (
            <span className="rounded-sm border border-attention-meaningful/50 bg-attention-meaningful/10 px-2.5 py-0.5 text-xs font-medium text-attention-meaningful">
              Market already moved
            </span>
          ) : null}
        </div>
        <AttentionBadge level={level} />
      </div>

      {signal.title ? (
        <h2 className="font-serif text-2xl font-semibold leading-snug text-foreground">{signal.title}</h2>
      ) : null}
      {signal.summary ? (
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{signal.summary}</p>
      ) : null}

      <div className="mt-5 flex flex-wrap gap-x-8 gap-y-3 border-t border-border pt-5">
        <GlanceStat
          label="Direction"
          value={titleize(signal.direction)}
          className={directionClass(signal.direction)}
        />
        {/* <GlanceStat label="Potential impact" value={titleize(signal.potential_impact)} />
        <GlanceStat label="Confidence" value={confidence} /> */}
        <GlanceStat
          label="Potential impact"
          value={titleize(signal.potential_impact)}
          className={impactClass(signal.potential_impact)}
        />
        <GlanceStat label="Confidence" value={confidence} className="text-primary" />
        {showTimeHorizon ? (
          <GlanceStat label="Time horizon" value={titleize(signal.time_horizon)} />
        ) : null}
      </div>

      {/* {hasDetail ? (
        <Disclosure summary="Details"> */}
          {/* <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4"> */}
          {/* <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4"> */}
            {/* <Meta label="Time horizon" value={titleize(signal.time_horizon)} />
            <Meta label="Sentiment" value={titleize(signal.sentiment)} />
            <Meta label="Source agreement" value={titleize(signal.source_agreement)} />
            <Meta label="First seen" value={formatDateTime(signal.first_evidence_at)} />
            <Meta label="Latest evidence" value={formatDateTime(signal.latest_evidence_at)} /> */}
          {/* </dl> */}
          {/* {entities.length > 0 ? (
            <div className="mt-4">
              <p className="label-caps">Affected</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {entities.map((entity, i) => (
                  <span
                    key={`${entity}-${i}`}
                    className="rounded border border-border px-2 py-0.5 text-xs text-foreground"
                  >
                    {entity}
                  </span>
                ))}
              </div>
            </div>
          ) : null} */}
        {/* </Disclosure>
      ) : null} */}

      {evidence.length > 0 ? (
        <Disclosure
          summary={`Evidence${
            typeof signal.evidence_count === "number" ? ` (${signal.evidence_count})` : ""
          }`}
        >
          <ul className="space-y-2">
            {evidence.map((item, i) => {
              const published = formatDate(item.published_at);
              // const label = [item.source, item.title].filter(Boolean).join(" · ");
              const label = [item.source, item.title].filter(hasText).join(" · ");
              const text = [label, published].filter(Boolean).join(" · ");
              if (!text) return null;
              return (
                <li key={i} className="text-sm leading-relaxed">
                  {item.url ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-foreground underline decoration-border underline-offset-4 hover:decoration-foreground"
                    >
                      {text}
                    </a>
                  ) : (
                    <span className="text-foreground">{text}</span>
                  )}
                </li>
              );
            })}
          </ul>
        </Disclosure>
      ) : (
        <p className="mt-5 border-t border-border pt-5 text-sm text-muted-foreground">
          No supporting evidence was provided for this development.
        </p>
      )}
    </article>
  );
}