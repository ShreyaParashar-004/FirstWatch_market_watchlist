import { Link, useNavigate } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import { useAuth } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ThemeProvider } from "@/lib/theme";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Bell } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, asList } from "@/lib/api";
import type { Notification } from "@/lib/types";
import { toast } from "sonner";
import { useRef } from "react";

const nav = [
  { to: "/", label: "Developmets" },
  { to: "/tracking", label: "Tracking" },
  { to: "/watchlist", label: "Watchlist" },
] as const;

function ConfigNotice() {
  if (API_BASE_URL) return null;
  return (
    <div className="border-b border-destructive/30 bg-destructive/5 px-6 py-2 text-center text-xs text-foreground">
      The service address isn&apos;t configured. Set <code>VITE_API_BASE_URL</code> to your FastAPI
      backend URL.
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => asList<Notification>(await api.notifications()),
    enabled: isAuthenticated,
    refetchInterval: 30000,
  });
  const readNotification = useMutation({
    mutationFn: (id: number) => api.readNotification(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });
  const notificationItems = notifications.data ?? [];
  const unread = notificationItems.filter((item) => !item.read_at);
  const knownNotificationIds = useRef<Set<number> | null>(null);

  useEffect(() => {
    if (!notifications.data) return;
    const current = new Set(notifications.data.map((item) => item.id));
    if (knownNotificationIds.current) {
      notifications.data
        .filter((item) => !knownNotificationIds.current?.has(item.id))
        .forEach((item) => {
          toast(item.title, {
            description: item.watch_label,
            action: {
              label: "Open",
              onClick: () => {
                readNotification.mutate(item.id);
                navigate({ to: "/", hash: `signal-${item.signal_id}` });
              },
            },
          });
        });
    }
    knownNotificationIds.current = current;
  }, [notifications.data, navigate, readNotification]);

  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background">
        <ConfigNotice />
        <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur">
          <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-6">
            <Link to="/" className="flex items-baseline gap-2">
              <span className="font-serif text-xl tracking-tight text-foreground">FirstWatch</span>
              <span className="hidden text-[11px] tracking-[0.14em] text-muted-foreground uppercase sm:inline">
                Market intelligence
              </span>
            </Link>

            <nav className="flex items-center gap-1" aria-label="Main">
              {nav.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  activeOptions={{ exact: item.to === "/" }}
                  className="rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
                  activeProps={{ className: "bg-primary text-primary-foreground font-medium" }}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            <div className="flex items-center gap-2">
              <ThemeToggle />
              {isAuthenticated ? (
                <>
                  <details className="relative">
                    <summary className="flex cursor-pointer list-none items-center rounded-md border border-border bg-secondary/50 p-2 text-muted-foreground hover:bg-secondary hover:text-foreground">                      <Bell className="size-4" aria-label="Notifications" />
                      {unread.length > 0 ? (
                        <span className="ml-1 rounded-full bg-destructive px-1.5 text-[10px] text-destructive-foreground">
                          {unread.length}
                        </span>
                      ) : null}
                    </summary>
                    <div className="absolute right-0 z-30 mt-2 w-80 rounded-md border border-border bg-card p-2 shadow-lg">
                      {notificationItems.length === 0 ? (
                        <p className="p-3 text-sm text-muted-foreground">No notifications.</p>
                      ) : (
                        notificationItems.map((item) => (
                          <button
                            key={item.id}
                            className="block w-full rounded p-3 text-left text-sm hover:bg-secondary"
                            onClick={() => {
                              readNotification.mutate(item.id);
                              navigate({ to: "/", hash: `signal-${item.signal_id}` });
                            }}
                          >
                            <span className="font-medium text-foreground">{item.title}</span>
                            <span className="mt-1 block text-xs text-muted-foreground">
                              {item.watch_label}
                            </span>
                          </button>
                        ))
                      )}
                    </div>
                  </details>
                  <span className="hidden max-w-[16ch] truncate text-xs text-muted-foreground md:inline">
                    {typeof user?.["email"] === "string" ? (user["email"] as string) : "Signed in"}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      logout();
                      navigate({ to: "/auth" });
                    }}
                  >
                    Sign out
                  </Button>
                </>
              ) : null}
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-6 py-12">{children}</main>

        <footer className="border-t border-border px-6 py-8 text-center text-xs text-muted-foreground">
          FirstWatch shows only what the service reports.
        </footer>
      </div>
    </ThemeProvider>
  );
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { ready, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (ready && !isAuthenticated) navigate({ to: "/auth" });
  }, [ready, isAuthenticated, navigate]);

  if (!ready) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <p className="text-sm text-muted-foreground">Loading…</p>
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return <AppShell>{children}</AppShell>;
}