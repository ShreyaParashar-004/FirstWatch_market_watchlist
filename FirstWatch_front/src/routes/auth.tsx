import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { API_BASE_URL, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export const Route = createFileRoute("/auth")({
  head: () => ({
    meta: [
      { title: "Sign in — FirstWatch" },
      {
        name: "description",
        content:
          "Sign in to FirstWatch to see what is starting to matter across the companies and themes you watch.",
      },
      { property: "og:title", content: "Sign in — FirstWatch" },
      {
        property: "og:description",
        content: "Access your FirstWatch signals, tracking and watchlist.",
      },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const { login, register, isAuthenticated, ready } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    if (ready && isAuthenticated) navigate({ to: "/" });
  }, [ready, isAuthenticated, navigate]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setPending(true);
    try {
      if (mode === "login") await login(email, password);
      else await register(email, password);
      navigate({ to: "/" });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401 && mode === "login") {
        setError("That email and password combination wasn't recognised.");
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden flex-col border-r border-border bg-surface px-12 py-14 lg:flex">
        <span className="font-serif text-xl tracking-tight text-foreground">FirstWatch</span>
        <div className="mt-16 max-w-md">
          <h1 className="font-serif text-4xl leading-tight text-foreground">
            Your market watchlist, in one place.
          </h1>
          <p className="mt-6 text-sm leading-relaxed text-muted-foreground">
            Track the companies and themes you care about. See recent developments and market
            movement.
          </p>
        </div>
        {/* <p className="text-xs text-muted-foreground">Market intelligence, quietly.</p> */}
      </section>

      <section className="flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <h2 className="font-serif text-2xl text-foreground">
            {mode === "login" ? "Sign in" : "Create your account"}
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {mode === "login"
              ? "Continue to your watchlist."
              : "Start watching the companies and themes you care about."}
          </p>

          {!API_BASE_URL ? (
            <p className="mt-6 rounded-md border border-destructive/30 bg-destructive/5 p-3 text-xs text-foreground">
              The service address isn&apos;t configured yet. Set <code>VITE_API_BASE_URL</code> to
              your FastAPI backend URL.
            </p>
          ) : null}

          <form onSubmit={onSubmit} className="mt-8 space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}

            <Button type="submit" className="w-full" disabled={pending}>
              {pending
                ? mode === "login"
                  ? "Signing in…"
                  : "Creating account…"
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
            </Button>
          </form>

          <button
            type="button"
            className="mt-6 text-sm text-muted-foreground underline underline-offset-4 hover:text-foreground"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError(null);
            }}
          >
            {mode === "login"
              ? "No account yet? Create one"
              : "Already have an account? Sign in"}
          </button>
        </div>
      </section>
    </div>
  );
}
