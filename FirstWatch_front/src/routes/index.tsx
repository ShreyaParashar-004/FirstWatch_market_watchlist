import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { RequireAuth } from "@/components/AppShell";
import { SignalCard } from "@/components/SignalCard";
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/States";
import { Button } from "@/components/ui/button";
import { api, asList } from "@/lib/api";
import { attentionLevel } from "@/lib/format";
import type { Signal } from "@/lib/types";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Recent Developments — What is starting to matter | FirstWatch" },
      {
        name: "description",
        content:
          "Emerging news and its potential implications for the companies and themes on your FirstWatch watchlist.",
      },
      { property: "og:title", content: "Recent Developments — What is starting to matter | FirstWatch" },
      {
        property: "og:description",
        content: "Emerging market intelligence for the companies and themes you watch.",
      },
    ],
  }),
  component: () => (
    <RequireAuth>
      <SignalsPage />
    </RequireAuth>
  ),
});

const order = { high: 0, meaningful: 1, worth_watching: 2, normal: 3 } as const;

function SignalsPage() {
  const queryClient = useQueryClient();
  const [refreshError, setRefreshError] = useState<string | null>(null);

  const query = useQuery({
    queryKey: ["signals"],
    queryFn: async () => asList<Signal>(await api.signals()),
  });

  const refresh = useMutation({
    mutationFn: () => api.refreshSignals(),
    onSuccess: () => {
      setRefreshError(null);
      queryClient.invalidateQueries({ queryKey: ["signals"] });
    },
    onError: (error: unknown) =>
      setRefreshError(error instanceof Error ? error.message : "Refresh failed."),
  });

  const signals = [...(query.data ?? [])].sort(
    (a, b) => order[attentionLevel(a)] - order[attentionLevel(b)],
  );

  return (
    <>
      <PageHeader
        eyebrow="Developments"
        title="What is starting to matter?"
        description="Emerging information and potential implications for what you watch."
        action={
          <Button
            variant="outline"
            onClick={() => refresh.mutate()}
            disabled={refresh.isPending || query.isFetching}
          >
            {refresh.isPending ? "Refreshing…" : "Refresh intelligence"}
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
          message={query.error instanceof Error ? query.error.message : "Couldn't load."}
          onRetry={() => query.refetch()}
        />
      ) : signals.length === 0 ? (
        <EmptyState
          title="Nothing meaningful detected yet."
          description="New developments appear here once something emerges for the companies and themes on your watchlist."
        />
      ) : (
        <div className="space-y-5">
          {signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      )}
    </>
  );
}
