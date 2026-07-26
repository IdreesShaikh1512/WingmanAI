"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { useAuthStore } from "@/lib/auth-store";
import { api } from "@/lib/api";

const OBJECTIVES = [
  "Plan my Japan trip to Tokyo for 10 days, budget $3000, solo",
  "Prepare me for a System Design interview",
  "Launch a micro-SaaS in 30 days",
  "Become a cybersecurity expert",
  "Build a Netflix Clone using React and FastAPI",
];

export default function LandingPage() {
  const router = useRouter();
  const { setSession } = useAuthStore();
  const [objectiveIdx, setObjectiveIdx] = useState(0);
  const [displayed, setDisplayed] = useState("");
  const [typing, setTyping] = useState(true);
  const [userInput, setUserInput] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Typewriter animation when not focused
  useEffect(() => {
    if (isFocused || userInput) return;
    const target = OBJECTIVES[objectiveIdx];
    let i = 0;
    setDisplayed("");
    setTyping(true);
    const interval = setInterval(() => {
      i++;
      setDisplayed(target.slice(0, i));
      if (i >= target.length) {
        clearInterval(interval);
        setTyping(false);
        setTimeout(() => setObjectiveIdx((p) => (p + 1) % OBJECTIVES.length), 2500);
      }
    }, 35);
    return () => clearInterval(interval);
  }, [objectiveIdx, isFocused, userInput]);

  // Fast guest login + navigate to mission control
  async function launchObjective(objective: string) {
    if (!objective.trim() || isSubmitting) return;
    setIsSubmitting(true);

    try {
      // Ensure user session exists
      const testEmail = "testuser_intelligence@wingman.os";
      const testPass = "SecurePassword123!";

      let tokens;
      try {
        tokens = await api.login(testEmail, testPass);
      } catch {
        await api.register(testEmail, testPass, "Autonomous User");
        tokens = await api.login(testEmail, testPass);
      }

      const user = await api.getMe(tokens.access_token);
      setSession(tokens.access_token, user);

      // Navigate to mission control with pre-filled objective
      const encoded = encodeURIComponent(objective.trim());
      router.push(`/mission-control?initialObjective=${encoded}`);
    } catch {
      // Fallback: route directly to mission control
      router.push("/mission-control");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const finalQuery = userInput.trim() || displayed;
    launchObjective(finalQuery);
  }

  return (
    <main className="min-h-screen bg-state-idle flex flex-col relative overflow-hidden text-white">
      {/* Ambient glowing background orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div
          className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)" }}
        />
        <div
          className="absolute bottom-[-5%] right-[10%] w-[500px] h-[500px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(139,92,246,0.07) 0%, transparent 70%)" }}
        />
        <div
          className="absolute top-[40%] left-[-5%] w-[400px] h-[400px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(59,130,246,0.06) 0%, transparent 70%)" }}
        />
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-5">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => router.push("/")}>
          <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-pulse" style={{ boxShadow: "0 0 14px rgba(245,158,11,0.9)" }} />
          <span className="mono text-xs tracking-[0.3em] text-amber-400 uppercase font-bold">WINGMAN OS</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-white/60 hover:text-white text-sm transition px-4 py-2">
            Sign in
          </Link>
          <button
            onClick={() => launchObjective(displayed || OBJECTIVES[0])}
            className="btn-primary text-sm px-5 py-2.5 rounded-lg shadow-lg hover:shadow-amber-500/20"
          >
            Begin Mission
          </button>
        </div>
      </nav>

      {/* Hero Content */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center -mt-6">
        <div className="animate-fade-up">
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-8 text-xs mono text-white/70 border border-white/10">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            AI Operating System · Autonomous Reasoning Engine · Active
          </div>
        </div>

        <h1 className="animate-fade-up text-5xl sm:text-7xl font-bold tracking-tight leading-none mb-6 max-w-4xl">
          You express.
          <br />
          <span className="text-gradient-amber">Wingman executes.</span>
        </h1>

        <p className="animate-fade-up text-white/50 text-lg max-w-xl leading-relaxed mb-10">
          State any goal. Wingman routes intent, asks clarifying questions when needed, generates domain missions, and produces rich artifacts.
        </p>

        {/* REAL INTERACTIVE OBJECTIVE INPUT BOX */}
        <form onSubmit={handleSubmit} className="animate-fade-up w-full max-w-2xl mb-8">
          <div className="glass rounded-2xl p-2 flex items-center gap-3 border border-amber-400/20 shadow-2xl focus-within:border-amber-400/50 transition">
            <div className="w-10 h-10 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center shrink-0 ml-1">
              <span className="text-amber-400 text-lg">⚡</span>
            </div>
            
            <input
              type="text"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              placeholder={isFocused ? "Type your objective (e.g. Plan my Japan trip, Learn SQL)..." : displayed || "State your objective..."}
              className="flex-1 bg-transparent text-white text-base outline-none placeholder:text-white/40 px-2 py-3 font-sans"
            />

            <button
              type="submit"
              disabled={isSubmitting}
              className="btn-primary px-6 py-3 text-sm rounded-xl shrink-0 font-medium disabled:opacity-50"
            >
              {isSubmitting ? "Launching..." : "Execute →"}
            </button>
          </div>
        </form>

        {/* Quick Suggestion Chips */}
        <div className="animate-fade-up flex flex-wrap justify-center gap-2 max-w-2xl mb-12">
          {OBJECTIVES.map((obj) => (
            <button
              key={obj}
              onClick={() => launchObjective(obj)}
              className="glass px-3.5 py-1.5 rounded-full text-xs text-white/60 hover:text-white hover:border-amber-400/40 hover:bg-amber-400/5 transition text-left"
            >
              + {obj}
            </button>
          ))}
        </div>

        <div className="animate-fade-up flex flex-col sm:flex-row items-center gap-4">
          <button
            onClick={() => launchObjective(userInput || displayed || "Plan my Japan trip")}
            className="btn-primary px-8 py-3.5 text-base rounded-xl"
          >
            Launch Mission Control →
          </button>
          <Link href="/login" className="glass px-8 py-3.5 text-base rounded-xl text-white/70 hover:text-white transition">
            Sign in to mission
          </Link>
        </div>
      </div>

      {/* Interactive Execution Flow */}
      <div className="animate-fade-up relative z-10 py-12 px-6 border-t border-white/[0.06]">
        <p className="text-center mono text-xs text-white/30 uppercase tracking-[0.25em] mb-8">
          Autonomous Architecture Pipeline
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap max-w-4xl mx-auto">
          {[
            { label: "Intent Router", desc: "20+ Domains", color: "amber" },
            { label: "Gatekeeper", desc: "Clarification Check", color: "blue" },
            { label: "Mission Planner", desc: "Domain Operations", color: "violet" },
            { label: "Artifact Engine", desc: "Roadmaps & Schemas", color: "green" },
            { label: "Memory Sync", desc: "Fact Storage", color: "amber" },
            { label: "Next Action", desc: "Proactive Suggestions", color: "green" },
          ].map((node, i) => (
            <div
              key={node.label}
              onClick={() => launchObjective(`Demonstrate ${node.label} feature`)}
              className="glass rounded-xl px-4 py-3 text-left cursor-pointer hover:border-amber-400/40 transition group"
            >
              <p className="mono text-xs font-bold text-amber-400 group-hover:text-amber-300 transition">
                {node.label}
              </p>
              <p className="text-[11px] text-white/40 mt-0.5">{node.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
