import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import { RequireAuth } from "@/components/AppShell";
import { EmptyState, ErrorState, LoadingRows, PageHeader } from "@/components/States";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, asList } from "@/lib/api";
import type { WatchCompany, WatchTheme } from "@/lib/types";

export const Route = createFileRoute("/watchlist")({
  head: () => ({
    meta: [
      { title: "Watchlist — Companies and themes | FirstWatch" },
      {
        name: "description",
        content:
          "Choose the companies and themes FirstWatch should watch. Nothing is added without you.",
      },
      { property: "og:title", content: "Watchlist — Companies and themes | FirstWatch" },
      {
        property: "og:description",
        content: "Add or remove the tickers and themes you want FirstWatch to watch.",
      },
    ],
  }),
  component: () => (
    <RequireAuth>
      <WatchlistPage />
    </RequireAuth>
  ),
});

// ---------------------------------------------------------------------------
// Local suggestion hints only.
//
// The backend has no company-search / lookup / trending endpoint, so this is
// NOT a validated company database and NOT market data — it's a small,
// static list of well-known names used purely to make common tickers easier
// to find while typing. Nothing here is sent to the backend directly; only
// the resolved ticker (or theme name/keyword) is submitted, exactly as
// before. Manual entry of anything not in this list is always supported.
// ---------------------------------------------------------------------------
const COMPANY_HINTS: { ticker: string; name: string }[] = [
  { ticker: "AAPL", name: "Apple Inc." },
  { ticker: "MSFT", name: "Microsoft Corporation" },
  { ticker: "GOOGL", name: "Alphabet Inc." },
  { ticker: "AMZN", name: "Amazon.com Inc." },
  { ticker: "TSLA", name: "Tesla Inc." },
  { ticker: "NVDA", name: "NVIDIA Corporation" },
  { ticker: "META", name: "Meta Platforms Inc." },
  { ticker: "NFLX", name: "Netflix Inc." },
  { ticker: "JPM", name: "JPMorgan Chase & Co." },
  { ticker: "V", name: "Visa Inc." },
  { ticker: "RELIANCE", name: "Reliance Industries Ltd." },
  { ticker: "TCS", name: "Tata Consultancy Services Ltd." },
  { ticker: "INFY", name: "Infosys Ltd." },
  { ticker: "HDFCBANK", name: "HDFC Bank Ltd." },
  { ticker: "SUNPHARMA", name: "Sun Pharmaceutical Industries Ltd." },
  { ticker: "ICICIBANK", name: "ICICI Bank Ltd." },
  { ticker: "ITC", name: "ITC Ltd." },
  { ticker: "HINDUNILVR", name: "Hindustan Unilever Ltd." },
  { ticker: "BHARTIARTL", name: "Bharti Airtel Ltd." },
  { ticker: "WIPRO", name: "Wipro Ltd." },
];

const THEME_HINTS: { name: string; keywords: string[] }[] = [
  { name: "Solar power", keywords: ["solar", "sustainable energy", "battery storage"] },
  { name: "Electric vehicles", keywords: ["EV", "battery storage", "charging infrastructure"] },
  { name: "Artificial intelligence", keywords: ["AI", "machine learning", "generative AI"] },
  { name: "Semiconductors", keywords: ["chips", "foundry", "AI hardware"] },
  { name: "Renewable energy", keywords: ["solar", "wind", "battery storage"] },
  { name: "Pharmaceuticals", keywords: ["generic drugs", "biotech", "healthcare"] },
];

function splitKeywords(value?: string | null): string[] {
  if (!value) return [];
  return value
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
}

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-border bg-card p-6">
      <h2 className="font-serif text-xl text-foreground">{title}</h2>
      <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
      <div className="mt-6">{children}</div>
    </section>
  );
}

function Row({
  label,
  sub,
  keywords,
  onRemove,
  removing,
}: {
  label: string;
  sub?: string | null;
  keywords?: string[];
  onRemove: () => void;
  removing: boolean;
}) {
  return (
    <li className="flex items-center justify-between gap-4 rounded-md border-b border-border px-1 py-3 transition-colors last:border-b-0 hover:bg-secondary/40">
      <div>
        <p className="text-sm font-medium text-foreground">{label}</p>
        {sub ? <p className="mt-0.5 text-xs text-muted-foreground">{sub}</p> : null}
        {keywords && keywords.length > 0 ? (
          <ul className="mt-1.5 flex flex-wrap gap-1.5">
            {keywords.map((k) => (
              <li
                key={k}
                className="rounded-sm border border-border px-2 py-0.5 text-[11px] text-muted-foreground"
              >
                {k}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
      <Button variant="ghost" size="sm" onClick={onRemove} disabled={removing}>
        {removing ? "Removing…" : "Remove"}
      </Button>
    </li>
  );
}

/** Small dropdown of suggestions shown below an input, closed by default (progressive disclosure). */
function SuggestionList<T>({
  items,
  heading,
  renderLabel,
  renderSub,
  onPick,
}: {
  items: T[];
  heading: string;
  renderLabel: (item: T) => string;
  renderSub?: (item: T) => string | undefined;
  onPick: (item: T) => void;
}) {
  if (items.length === 0) return null;
  return (
    <ul className="absolute z-10 mt-1 w-full overflow-hidden rounded-md border border-border bg-card shadow-lg">
      <li className="border-b border-border px-3 py-1.5 text-[11px] tracking-wide text-muted-foreground uppercase">
        {heading}
      </li>
      {items.map((item, i) => (
        <li key={i}>
          <button
            type="button"
            // onMouseDown (not onClick) so the button fires before the input's onBlur closes the list
            onMouseDown={(e) => {
              e.preventDefault();
              onPick(item);
            }}
            className="block w-full px-3 py-2 text-left text-sm text-foreground hover:bg-secondary"
          >
            {renderLabel(item)}
            {renderSub?.(item) ? (
              <span className="ml-2 text-xs text-muted-foreground">{renderSub(item)}</span>
            ) : null}
          </button>
        </li>
      ))}
    </ul>
  );
}

function WatchlistPage() {
  const queryClient = useQueryClient();

  // Companies -----------------------------------------------------------
  const [companyQuery, setCompanyQuery] = useState("");
  const [selectedCompany, setSelectedCompany] = useState<{ ticker: string; name: string } | null>(
    null,
  );
  const [companySuggestionsOpen, setCompanySuggestionsOpen] = useState(false);
  const [companyError, setCompanyError] = useState<string | null>(null);

  const companySuggestions = useMemo(() => {
    const q = companyQuery.trim().toLowerCase();
    if (!q) return COMPANY_HINTS.slice(0, 6); // common suggestions, shown on empty focus
    return COMPANY_HINTS.filter(
      (c) => c.ticker.toLowerCase().includes(q) || c.name.toLowerCase().includes(q),
    ).slice(0, 8);
  }, [companyQuery]);

  // Themes ----------------------------------------------------------------
  const [themeQuery, setThemeQuery] = useState("");
  const [selectedTheme, setSelectedTheme] = useState<{ name: string; keywords: string[] } | null>(
    null,
  );
  const [themeSuggestionsOpen, setThemeSuggestionsOpen] = useState(false);
  const [showKeywordsField, setShowKeywordsField] = useState(false);
  const [keywordsInput, setKeywordsInput] = useState("");
  const [themeError, setThemeError] = useState<string | null>(null);
  const keywordsInputRef = useRef<HTMLInputElement>(null);

  const themeSuggestions = useMemo(() => {
    const q = themeQuery.trim().toLowerCase();
    if (!q) return THEME_HINTS.slice(0, 6);
    return THEME_HINTS.filter(
      (t) =>
        t.name.toLowerCase().includes(q) || t.keywords.some((k) => k.toLowerCase().includes(q)),
    ).slice(0, 8);
  }, [themeQuery]);

  const companies = useQuery({
    queryKey: ["companies"],
    queryFn: async () => asList<WatchCompany>(await api.companies()),
  });
  const themes = useQuery({
    queryKey: ["themes"],
    queryFn: async () => asList<WatchTheme>(await api.themes()),
  });

  const addCompany = useMutation({
    mutationFn: (value: string) => api.addCompany({ ticker: value.toUpperCase() }),
    onSuccess: () => {
      setCompanyQuery("");
      setSelectedCompany(null);
      setCompanyError(null);
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["tracking"] });
    },
    onError: (error: unknown) =>
      setCompanyError(error instanceof Error ? error.message : "Couldn't add that company."),
  });

  const removeCompany = useMutation({
    mutationFn: (id: number | string) => api.removeCompany(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["companies"] });
      queryClient.invalidateQueries({ queryKey: ["tracking"] });
    },
    onError: (error: unknown) =>
      setCompanyError(error instanceof Error ? error.message : "Couldn't remove that company."),
  });

  const addTheme = useMutation({
    mutationFn: ({ name, keyword }: { name: string; keyword: string }) =>
      api.addTheme(name, keyword),
    onSuccess: () => {
      setThemeQuery("");
      setSelectedTheme(null);
      setKeywordsInput("");
      setShowKeywordsField(false);
      setThemeError(null);
      queryClient.invalidateQueries({ queryKey: ["themes"] });
    },
    onError: (error: unknown) =>
      setThemeError(error instanceof Error ? error.message : "Couldn't add that theme."),
  });

  const removeTheme = useMutation({
    mutationFn: (id: number | string) => api.removeTheme(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["themes"] }),
    onError: (error: unknown) =>
      setThemeError(error instanceof Error ? error.message : "Couldn't remove that theme."),
  });

  const companyList = companies.data ?? [];
  const themeList = themes.data ?? [];

  function submitCompany() {
    const ticker = selectedCompany ? selectedCompany.ticker : companyQuery.trim();
    if (!ticker) return;
    addCompany.mutate(ticker);
  }

  function submitTheme() {
    const name = selectedTheme ? selectedTheme.name : themeQuery.trim();
    if (!name) return;
    const customKeywords = keywordsInput.trim();
    const fallbackKeywords = selectedTheme ? selectedTheme.keywords.join(", ") : "";
    const keyword = customKeywords || fallbackKeywords || name;
    addTheme.mutate({ name, keyword });
  }

  return (
    <>
      <PageHeader
        eyebrow="Watchlist"
        title="What you watch"
        description="You decide what FirstWatch pays attention to. Nothing is ever added for you."
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <Section title="Companies" description="Tickers such as AAPL or TSLA.">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              submitCompany();
            }}
          >
            <div className="relative flex-1">
              <Input
                aria-label="Company ticker or name"
                placeholder="Search or enter a ticker"
                value={
                  selectedCompany
                    ? `${selectedCompany.ticker} — ${selectedCompany.name}`
                    : companyQuery
                }
                onFocus={() => setCompanySuggestionsOpen(true)}
                onBlur={() => setCompanySuggestionsOpen(false)}
                onChange={(e) => {
                  // Editing the text after a selection breaks the lock and
                  // returns to plain manual entry, so the displayed name can
                  // never drift from what will actually be submitted.
                  setSelectedCompany(null);
                  setCompanyQuery(e.target.value);
                }}
              />
              {companySuggestionsOpen ? (
                <SuggestionList
                  items={companySuggestions}
                  heading="Suggestions"
                  renderLabel={(c) => c.ticker}
                  renderSub={(c) => c.name}
                  onPick={(c) => {
                    setSelectedCompany(c);
                    setCompanyQuery(c.ticker);
                    setCompanySuggestionsOpen(false);
                  }}
                />
              ) : null}
            </div>
            <Button
              type="submit"
              disabled={addCompany.isPending || !(selectedCompany || companyQuery.trim())}
            >
              {addCompany.isPending ? "Adding…" : "Add"}
            </Button>
          </form>
          {companyError ? (
            <p role="alert" className="mt-3 text-sm text-destructive">
              {companyError}
            </p>
          ) : null}

          <div className="mt-5">
            {companies.isLoading ? (
              <LoadingRows rows={2} />
            ) : companies.isError ? (
              <ErrorState
                message={
                  companies.error instanceof Error
                    ? companies.error.message
                    : "Companies couldn't load."
                }
                onRetry={() => companies.refetch()}
              />
            ) : companyList.length === 0 ? (
              <EmptyState
                title="No companies yet."
                description="Add a company or theme to start watching what matters."
              />
            ) : (
              <ul>
                {companyList.map((company) => (
                  <Row
                    key={company.id}
                    label={company.ticker ?? company.name ?? `#${company.id}`}
                    sub={company.ticker && company.name ? company.name : null}
                    onRemove={() => removeCompany.mutate(company.id)}
                    removing={removeCompany.isPending && removeCompany.variables === company.id}
                  />
                ))}
              </ul>
            )}
          </div>
        </Section>

        <Section
          title="Themes"
          description="Keywords such as solar power, battery storage or recyclable materials."
        >
          <form
            className="space-y-2"
            onSubmit={(e) => {
              e.preventDefault();
              submitTheme();
            }}
          >
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  aria-label="Theme name"
                  placeholder="Add a theme"
                  value={selectedTheme ? selectedTheme.name : themeQuery}
                  onFocus={() => setThemeSuggestionsOpen(true)}
                  onBlur={() => setThemeSuggestionsOpen(false)}
                  onChange={(e) => {
                    setSelectedTheme(null);
                    setThemeQuery(e.target.value);
                  }}
                />
                {themeSuggestionsOpen ? (
                  <SuggestionList
                    items={themeSuggestions}
                    heading="Suggestions"
                    renderLabel={(t) => t.name}
                    renderSub={(t) => t.keywords.join(", ")}
                    onPick={(t) => {
                      setSelectedTheme(t);
                      setThemeQuery(t.name);
                      setKeywordsInput(t.keywords.join(", "));
                      setShowKeywordsField(true);
                      setThemeSuggestionsOpen(false);
                    }}
                  />
                ) : null}
              </div>
              <Button
                type="submit"
                disabled={addTheme.isPending || !(selectedTheme || themeQuery.trim())}
              >
                {addTheme.isPending ? "Adding…" : "Add"}
              </Button>
            </div>

            {showKeywordsField ? (
              <Input
                ref={keywordsInputRef}
                aria-label="Related keywords, comma separated"
                placeholder="Related keywords, comma separated (e.g. solar, battery storage)"
                value={keywordsInput}
                onChange={(e) => setKeywordsInput(e.target.value)}
              />
            ) : (
              <button
                type="button"
                className="text-xs text-muted-foreground underline-offset-2 hover:text-foreground hover:underline"
                onClick={() => {
                  setShowKeywordsField(true);
                  requestAnimationFrame(() => keywordsInputRef.current?.focus());
                }}
              >
                + Add related keywords
              </button>
            )}
          </form>
          {themeError ? (
            <p role="alert" className="mt-3 text-sm text-destructive">
              {themeError}
            </p>
          ) : null}

          <div className="mt-5">
            {themes.isLoading ? (
              <LoadingRows rows={2} />
            ) : themes.isError ? (
              <ErrorState
                message={
                  themes.error instanceof Error ? themes.error.message : "Themes couldn't load."
                }
                onRetry={() => themes.refetch()}
              />
            ) : themeList.length === 0 ? (
              <EmptyState
                title="No themes yet."
                description="Add a company or theme to start watching what matters."
              />
            ) : (
              <ul>
                {themeList.map((item) => {
                  const keywords = splitKeywords(item.keyword).filter((k) => k !== item.name);
                  return (
                    <Row
                      key={item.id}
                      label={item.name ?? item.keyword ?? `#${item.id}`}
                      keywords={keywords}
                      onRemove={() => removeTheme.mutate(item.id)}
                      removing={removeTheme.isPending && removeTheme.variables === item.id}
                    />
                  );
                })}
              </ul>
            )}
          </div>
        </Section>
      </div>
    </>
  );
}