"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

type AuthFormProps = {
  mode: "login" | "register";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await api.register(email, password, fullName || undefined);
      }
      const tokens = await api.login(email, password);
      const user = await api.getMe(tokens.access_token);
      setSession(tokens.access_token, user);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-4">
      {mode === "register" && (
        <div>
          <label className="block font-mono text-xs text-steel uppercase tracking-wide mb-1">Full name</label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full bg-panel border border-panelBorder rounded-md px-3 py-2 text-ink"
            placeholder="Ada Lovelace"
          />
        </div>
      )}
      <div>
        <label className="block font-mono text-xs text-steel uppercase tracking-wide mb-1">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full bg-panel border border-panelBorder rounded-md px-3 py-2 text-ink"
          placeholder="you@example.com"
        />
      </div>
      <div>
        <label className="block font-mono text-xs text-steel uppercase tracking-wide mb-1">Password</label>
        <input
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full bg-panel border border-panelBorder rounded-md px-3 py-2 text-ink"
          placeholder="At least 8 characters"
        />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-amber text-graphite font-medium px-4 py-2.5 rounded-md hover:brightness-110 transition disabled:opacity-50"
      >
        {isSubmitting ? "Working..." : mode === "login" ? "Sign in" : "Create account"}
      </button>
    </form>
  );
}
