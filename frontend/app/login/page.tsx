"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const tokens = await api.login(email, password);
      const user = await api.getMe(tokens.access_token);
      setSession(tokens.access_token, user);
      router.push("/mission-control");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Authentication failed. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-state-idle flex items-center justify-center px-4 relative overflow-hidden">
      <div className="pointer-events-none fixed inset-0">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(245,158,11,0.06) 0%, transparent 70%)" }} />
      </div>

      <div className="relative z-10 w-full max-w-sm animate-scale-in">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 mb-6">
            <span className="w-2 h-2 rounded-full bg-amber-400" style={{ boxShadow: "0 0 8px rgba(245,158,11,0.8)" }} />
            <span className="mono text-xs tracking-[0.3em] text-amber-400 uppercase">WINGMAN OS</span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Welcome back</h1>
          <p className="text-white/35 text-sm">Your objectives await.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mono text-xs text-white/30 uppercase tracking-wider block mb-2">Email</label>
            <input
              type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="input-os w-full px-4 py-3 text-sm"
            />
          </div>
          <div>
            <label className="mono text-xs text-white/30 uppercase tracking-wider block mb-2">Password</label>
            <input
              type="password" required value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              className="input-os w-full px-4 py-3 text-sm"
            />
          </div>

          {error && (
            <div className="glass rounded-lg px-4 py-3 text-red-400 text-xs mono border border-red-500/20">
              ⚠ {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 text-sm rounded-xl">
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-3 h-3 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                Authenticating...
              </span>
            ) : "Enter Mission Control →"}
          </button>
        </form>

        <p className="text-center text-white/25 text-xs mt-8">
          No account?{" "}
          <Link href="/register" className="text-amber-400 hover:text-amber-300 transition">
            Begin mission
          </Link>
        </p>
      </div>
    </main>
  );
}
