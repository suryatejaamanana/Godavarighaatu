"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { Brand } from "@/components/admin/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAdmin } from "@/hooks/use-admin";
import { ApiError } from "@/lib/api";
import { login } from "@/services/admin";

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const me = useAdmin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // already signed in (valid cookies) -> go straight to the dashboard
  useEffect(() => {
    if (me.data) router.replace("/admin/dashboard");
  }, [me.data, router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const admin = await login(email.trim(), password);
      queryClient.setQueryData(["me"], admin);
      router.replace("/admin/dashboard");
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 429
          ? "Too many attempts. Please wait a minute and try again."
          : err instanceof ApiError
            ? err.message
            : "Something went wrong. Please try again.",
      );
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-dvh items-center justify-center bg-gradient-to-b from-brand-red to-brand-orange p-4">
      <div className="w-full max-w-sm rounded-2xl bg-brand-cream p-6 shadow-xl sm:p-8">
        <div className="mb-6 rounded-xl bg-brand-red p-4 text-center">
          <Brand />
        </div>
        <h1 className="mb-1 text-xl font-semibold">Sign in</h1>
        <p className="mb-5 text-sm text-muted-foreground">Staff and administrators only.</p>
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-10"
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-10"
            />
          </div>
          {error && (
            <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          <Button type="submit" disabled={busy || !email || !password} className="h-10 w-full bg-brand-red text-brand-cream hover:bg-brand-red/90">
            {busy && <Loader2 className="animate-spin" />}
            Sign in
          </Button>
        </form>
      </div>
    </main>
  );
}
