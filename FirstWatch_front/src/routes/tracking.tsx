import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { RequireAuth } from "@/components/AppShell";
import { Disclosure } from "@/components/Disclosure";
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/States";
import { Button } from "@/components/ui/button";
import { api, asList } from "@/lib/api";
// import { formatDateTime, formatDate, formatPct, formatPrice, hoursSince } from "@/lib/format";
import { formatDateTime, formatDate, formatLastDataIST, formatPct, formatPrice, hoursSince } from "@/lib/format";
import type { Observation, Tracking } from "@/lib/types";

export const Route = createFileRoute("/tracking")({
  head: () => ({
    meta: [
      { title: "Tracking — What already changed | FirstWatch" },
      {
        name: "description",
        content:
          "Stored market observations and movements for the companies on your FirstWatch watchlist.",
      },
      { property: "og:title", content: "Tracking — What already changed | FirstWatch" },
      {
        property: "og:description",
        content: "Recorded price observations and movement for the companies you watch.",
      },
    ],
  }),
  component: () => (
    <RequireAuth>
      <TrackingPage />
    </RequireAuth>
  ),
});

const STALE_AFTER_HOURS = 24;

function StatusTag({ children, tone }: { children: string; tone: "muted" | "warn" | "alert" }) {
  const cls =
    tone === "alert"
      ? "border-attention-high/60 text-attention-high"
      : tone === "warn"
        ? "border-attention-meaningful/50 text-attention-meaningful"
        : "border-border text-muted-foreground";
  return (
    <span className={`rounded-sm border px-2.5 py-0.5 text-xs font-medium ${cls}}`}>
      {children}
    </span>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="label-caps">{label}</dt>
      <dd className="mt-1 text-sm text-foreground">{value ?? "Not available"}</dd>
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
  emphasize,
}: {
  label: string;
  value: string | null;
  tone: "positive" | "negative" | "neutral";
  emphasize?: boolean;
}) {
  if (!value) return null;
  const toneClass =
    tone === "positive" ? "text-positive" : tone === "negative" ? "text-negative" : "text-foreground";
  return (
    <div>
      <p className="label-caps">{label}</p>
      <p
        className={`mt-0.5 font-mono ${emphasize ? "text-2xl font-semibold" : "text-base font-medium"} ${toneClass}`}
      >
        {value}
      </p>
    </div>
  );
}

function netTone(net: number | null | undefined): "positive" | "negative" | "neutral" {
  if (net === null || net === undefined || net === 0) return "neutral";
  return net > 0 ? "positive" : "negative";
}

function TrackingChart({
  observations,
  tone,
}: {
  observations: Observation[];
  tone: "positive" | "negative" | "neutral";
}) {
  const points = observations
    .filter((o) => o.price !== null && o.observed_at)
    .map((o) => ({ time: o.observed_at as string, price: o.price as number }))
    .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());

  if (points.length < 2) return null;

  const stroke =
    tone === "positive"
      ? "var(--color-positive)"
      : tone === "negative"
        ? "var(--color-negative)"
        : "var(--color-muted-foreground)";

  return (
    <div className="mt-5 h-36 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="time"
            tickFormatter={(value: string) => formatDate(value) ?? ""}
            tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
            axisLine={{ stroke: "var(--color-border)" }}
            tickLine={false}
            minTickGap={40}
          />
          <YAxis
            width={56}
            tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
            axisLine={false}
            tickLine={false}
            domain={["auto", "auto"]}
            tickFormatter={(value: number) =>
              value.toLocaleString(undefined, { maximumFractionDigits: 2 })
            }
          />
          <Tooltip
            formatter={(value: number) => [
              value.toLocaleString(undefined, { maximumFractionDigits: 4 }),
              "Price",
            ]}
            labelFormatter={(value: string) => formatDateTime(value) ?? ""}
            contentStyle={{
              background: "var(--color-card)",
              border: "1px solid var(--color-border)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Line
            type="monotone"
            dataKey="price"
            stroke={stroke}
            strokeWidth={1.75}
            dot={false}
            activeDot={{ r: 3 }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function TrackingCard({ item }: { item: Tracking }) {
  const hasData = item.status !== "no_data" && item.latest_price !== null;
  const age = hoursSince(item.latest_observed_at);
  const stale = hasData && age !== null && age > (item.window_hours ?? STALE_AFTER_HOURS);
  const price = formatPrice(item.latest_price, item.currency);
  const net = formatPct(item.change?.net_pct ?? null);
  const range = formatPct(item.change?.range_pct ?? null);
  const tone = netTone(item.change?.net_pct);
  const observations = item.observations ?? [];

  return (
    <article className="rounded-lg border border-border bg-card p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-baseline gap-3">
          <h2 className="font-mono text-lg font-medium text-foreground">{item.ticker}</h2>
          {price ? <span className="text-lg text-foreground">{price}</span> : null}
        </div>
        <div className="flex flex-wrap gap-2">
          {!hasData ? <StatusTag tone="muted">No data</StatusTag> : null}
          {stale ? <StatusTag tone="warn">Stale data</StatusTag> : null}
          {item.significant_movement ? (
            <StatusTag tone="alert">Significant movement</StatusTag>
          ) : null}
          {item.change?.swing ? <StatusTag tone="warn">Swing</StatusTag> : null}
        </div>
      </div>

      {!hasData ? (
        <p className="mt-4 text-sm text-muted-foreground">
          {item.message ?? "Market data isn't available yet."}
        </p>
      ) : (
        <>
          <p className="mt-1 text-xs text-muted-foreground">
            Last data: {formatLastDataIST(item.latest_observed_at) ?? "Not available"}
         </p>
          <div className="mt-4 flex flex-wrap gap-x-8 gap-y-3 border-t border-border pt-4">
            <Stat label="Net change" value={net} tone={tone} emphasize />
            <Stat label="Range" value={range} tone="neutral" />
          </div>

          <TrackingChart observations={observations} tone={tone} />

          <Disclosure summary="Price detail">
            <dl className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
              <Field
                label="Window"
                value={item.window_hours !== null ? `${item.window_hours} hours` : null}
              />
              <Field label="Last observed" value={formatDateTime(item.latest_observed_at)} />
              <Field label="Start" value={formatPrice(item.change?.start_price, item.currency)} />
              <Field label="End" value={formatPrice(item.change?.end_price, item.currency)} />
              <Field label="Low" value={formatPrice(item.change?.min_price, item.currency)} />
              <Field label="High" value={formatPrice(item.change?.max_price, item.currency)} />
            </dl>
          </Disclosure>
        </>
      )}

      {observations.length > 0 ? (
        <Disclosure
          summary={`${observations.length} recorded observation${observations.length === 1 ? "" : "s"}`}
        >
          <ul className="space-y-1.5">
            {observations.map((observation, i) => (
              <li key={i} className="flex flex-wrap gap-x-3 text-sm text-muted-foreground">
                <span className="text-foreground">
                  {formatPrice(observation.price, observation.currency) ?? "Price unavailable"}
                </span>
                <span>{formatDateTime(observation.observed_at) ?? "Time unavailable"}</span>
                {observation.source ? <span>· {observation.source}</span> : null}
              </li>
            ))}
          </ul>
        </Disclosure>
      ) : null}
    </article>
  );
}

function TrackingPage() {
  const queryClient = useQueryClient();
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["tracking"],
    queryFn: async () => asList<Tracking>(await api.tracking()),
  });

  const refresh = useMutation({
    mutationFn: () => api.refreshTracking(),
    onSuccess: () => {
      setRefreshError(null);
      queryClient.invalidateQueries({ queryKey: ["tracking"] });
    },
    onError: (error: unknown) =>
      setRefreshError(error instanceof Error ? error.message : "Refresh failed."),
  });

  const items = query.data ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Tracking"
        title="What already changed?"
        description="Stored market observations for the companies you watch."
        action={
          <Button
            variant="outline"
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending || query.isFetching}
          >
            {refresh.isPending ? "Refreshing…" : "Refresh market data"}
          </Button>
        }
      />

      {refreshError ? (
        <p role="alert" className="mb-6 text-sm text-destructive">
          {refreshError}
        </p>
      ) : null}

      {query.isLoading ? (
        <LoadingRows />
      ) : query.isError ? (
        <ErrorState
          message={
            query.error instanceof Error ? query.error.message : "Tracking data couldn't load."
          }
          onRetry={() => query.refetch()}
        />
      ) : items.length === 0 ? (
        <EmptyState
          title="Market data isn't available yet."
          description="Add a company to your watchlist, then refresh market data."
        />
      ) : (
        <div className="space-y-5">
          {items.map((item) => (
            <TrackingCard key={item.ticker} item={item} />
          ))}
        </div>
      )}
    </>
  );
}