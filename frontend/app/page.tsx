"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

const OBJECTIVES = [
  "Plan my Japan trip for next month",
  "Prepare me for a System Design interview",
  "Launch a micro-SaaS in 30 days",
  "Become a cybersecurity expert",
  "Research competitors for my startup",
];

export default function LandingPage() {
  const [objectiveIdx, setObjectiveIdx] = useState(0);
  const [displayed, setDisplayed] = useState("");
  const [typing, setTyping] = useState(true);

  useEffect(() => {
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
        setTimeout(() => setObjectiveIdx((p) => (p + 1) % OBJECTIVES.length), 2200);
      }
    }, 38);
    return () => clearInterval(interval);
  }, [objectiveIdx]);

  return (
    <main className="min-h-screen bg-state-idle flex flex-col relative overflow-hidden">
      {/* Ambient orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute top-[-10%] left-[20%] w-[600px] h-[600px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(245,158,11,0.07) 0%, transparent 70%)" }} />
        <div className="absolute bottom-[-5%] right-[10%] w-[500px] h-[500px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)" }} />
        <div className="absolute top-[40%] left-[-5%] w-[400px] h-[400px] rounded-full"
          style={{ background: "radial-gradient(circle, rgba(59,130,246,0.05) 0%, transparent 70%)" }} />
      </div>

      {/* Nav */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-5">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" style={{ boxShadow: "0 0 12px rgba(245,158,11,0.8)" }} />
          <span className="mono text-xs tracking-[0.3em] text-amber-400 uppercase font-bold">WINGMAN OS</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-white/50 hover:text-white/80 text-sm transition px-4 py-2">Sign in</Link>
          <Link href="/register" className="btn-primary text-sm px-5 py-2.5 rounded-lg">
            Begin Mission
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center -mt-8">
        <div className="animate-fade-up" style={{ animationDelay: "0ms" }}>
          <div className="inline-flex items-center gap-2 glass px-4 py-2 rounded-full mb-8 text-xs mono text-white/50">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            AI Operating System · Autonomous Execution Engine · v1.0
          </div>
        </div>

        <h1 className="animate-fade-up text-5xl sm:text-7xl font-bold tracking-tight leading-none mb-6 max-w-4xl"
          style={{ animationDelay: "80ms" }}>
          You express.
          <br />
          <span className="text-gradient-amber">Wingman executes.</span>
        </h1>

        <p className="animate-fade-up text-white/40 text-lg max-w-xl leading-relaxed mb-12"
          style={{ animationDelay: "160ms" }}>
          Not a chatbot. Not a dashboard. An AI that decomposes any goal into
          a structured plan and executes it — agents, databases, artifacts, memory.
        </p>

        {/* Live typewriter objective display */}
        <div className="animate-fade-up w-full max-w-xl mb-10" style={{ animationDelay: "240ms" }}>
          <div className="glass rounded-xl px-5 py-4 flex items-center gap-3 border border-white/[0.06]">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
            <span className="text-left text-white/70 text-sm flex-1 min-h-[1.3em]">
              {displayed}
              {typing && <span className="inline-block w-[2px] h-4 bg-amber-400 ml-0.5 cursor-blink align-middle" />}
            </span>
          </div>
        </div>

        <div className="animate-fade-up flex flex-col sm:flex-row items-center gap-4" style={{ animationDelay: "320ms" }}>
          <Link href="/register" className="btn-primary px-8 py-3.5 text-base rounded-xl">
            Launch Wingman →
          </Link>
          <Link href="/login" className="glass px-8 py-3.5 text-base rounded-xl text-white/60 hover:text-white transition">
            Sign in to mission
          </Link>
        </div>

        <p className="animate-fade-up mono text-xs text-white/20 mt-6" style={{ animationDelay: "400ms" }}>
          Press <kbd className="px-1.5 py-0.5 glass rounded text-white/30">Ctrl</kbd> +{" "}
          <kbd className="px-1.5 py-0.5 glass rounded text-white/30">K</kbd> after signing in
        </p>
      </div>

      {/* Agent flow diagram */}
      <div className="animate-fade-up relative z-10 py-16 px-6 border-t border-white/[0.04]"
        style={{ animationDelay: "480ms" }}>
        <p className="text-center mono text-xs text-white/25 uppercase tracking-[0.25em] mb-10">
          AI Execution Engine
        </p>
        <div className="flex items-center justify-center gap-2 flex-wrap max-w-3xl mx-auto">
          {[
            { label: "Intent", color: "amber" },
            { label: "Planner", color: "blue" },
            { label: "Research", color: "violet" },
            { label: "Memory", color: "green" },
            { label: "Executor", color: "amber" },
            { label: "Database", color: "green" },
          ].map((node, i) => (
            <div key={node.label} className="flex items-center gap-2">
              <div className="glass rounded-lg px-4 py-2 text-xs mono"
                style={{ 
                  color: node.color === "amber" ? "var(--c-amber)" : node.color === "blue" ? "var(--c-blue)" : node.color === "green" ? "var(--c-green)" : "var(--c-violet)",
                  borderColor: node.color === "amber" ? "rgba(245,158,11,0.2)" : node.color === "blue" ? "rgba(59,130,246,0.2)" : node.color === "green" ? "rgba(16,185,129,0.2)" : "rgba(139,92,246,0.2)",
                  animationDelay: `${i * 0.3}s`
                }}>
                {node.label}
              </div>
              {i < 5 && <span className="text-white/15">→</span>}
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
