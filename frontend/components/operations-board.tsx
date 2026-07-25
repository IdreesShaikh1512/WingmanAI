"use client";
import { useEffect, useState, useRef } from "react";

export type OperationStatus = "pending" | "running" | "done";

export interface Operation {
  id: string;
  title: string;
  agent: string;
  agentColor: string;
  status: OperationStatus;
  progress: number;
  durationMs: number;
  completedAt?: string;
  output?: string;
}

export interface Mission {
  id: string;
  objective: string;
  intent: string;
  startedAt: string;
  operations: Operation[];
}

const AGENT_MAP: Record<string, string[]> = {
  travel:   ["Research Agent", "Travel Agent",   "Memory Agent",   "Executor Agent", "Database Agent", "Calendar Agent"],
  learning: ["Research Agent", "Planner Agent",  "Memory Agent",   "Executor Agent", "Database Agent"],
  career:   ["Research Agent", "Planner Agent",  "Memory Agent",   "Executor Agent", "Database Agent"],
  business: ["Research Agent", "Business Agent", "Planner Agent",  "Executor Agent", "Database Agent"],
  fitness:  ["Health Agent",   "Planner Agent",  "Memory Agent",   "Executor Agent", "Database Agent"],
  reminder: ["Intent Engine",  "Calendar Agent", "Memory Agent",   "Database Agent"],
  task:     ["Planner Agent",  "Memory Agent",   "Executor Agent", "Database Agent", "Monitor Agent"],
  general:  ["Intent Engine",  "Planner Agent",  "Memory Agent",   "Executor Agent", "Database Agent"],
};

const AGENT_COLORS: Record<string, string> = {
  "Research Agent": "#60a5fa",
  "Travel Agent":   "#a78bfa",
  "Memory Agent":   "#34d399",
  "Executor Agent": "#f59e0b",
  "Database Agent": "#10b981",
  "Calendar Agent": "#f472b6",
  "Planner Agent":  "#818cf8",
  "Business Agent": "#fb923c",
  "Health Agent":   "#4ade80",
  "Intent Engine":  "#f59e0b",
  "Monitor Agent":  "#94a3b8",
};

const OPERATION_OUTPUTS: Record<string, string> = {
  "Research Agent": "Indexed 12 knowledge sources",
  "Travel Agent":   "Retrieved 3 itinerary options",
  "Memory Agent":   "Stored 4 memory entries",
  "Executor Agent": "Dispatched 5 sub-operations",
  "Database Agent": "Written to PostgreSQL",
  "Calendar Agent": "Created calendar events",
  "Planner Agent":  "Generated action roadmap",
  "Business Agent": "Analyzed market data",
  "Health Agent":   "Computed fitness metrics",
  "Intent Engine":  "Classified intent: 94% confidence",
  "Monitor Agent":  "Verified completion state",
};

export function buildMission(
  objective: string,
  intent: string,
  steps: string[],
): Mission {
  const agents = AGENT_MAP[intent] ?? AGENT_MAP.general;
  return {
    id: crypto.randomUUID(),
    objective,
    intent,
    startedAt: new Date().toISOString(),
    operations: steps.map((step, i) => {
      const agent = agents[i % agents.length];
      return {
        id: crypto.randomUUID(),
        title: step,
        agent,
        agentColor: AGENT_COLORS[agent] ?? "#f59e0b",
        status: "pending",
        progress: 0,
        durationMs: 700 + Math.random() * 800,
        output: OPERATION_OUTPUTS[agent],
      };
    }),
  };
}

interface OperationsBoardProps {
  mission: Mission;
  onComplete?: () => void;
}

export function OperationsBoard({ mission, onComplete }: OperationsBoardProps) {
  const [ops, setOps] = useState<Operation[]>(() =>
    mission.operations.map((o) => ({ ...o, status: "pending", progress: 0 })),
  );
  const [current, setCurrent] = useState(0);
  const [allDone, setAllDone] = useState(false);
  const startedRef = useRef(false);

  // Reset on new mission
  useEffect(() => {
    setOps(mission.operations.map((o) => ({ ...o, status: "pending", progress: 0 })));
    setCurrent(0);
    setAllDone(false);
    startedRef.current = false;
  }, [mission.id]);

  // Drive each operation
  useEffect(() => {
    if (allDone || current >= ops.length) return;

    // Mark running
    setOps((prev) =>
      prev.map((o, i) => (i === current ? { ...o, status: "running" } : o)),
    );

    const dur = ops[current]?.durationMs ?? 800;
    const STEPS = 25;
    const tick = dur / STEPS;
    let step = 0;

    const interval = setInterval(() => {
      step++;
      const progress = Math.min(100, (step / STEPS) * 100);
      setOps((prev) =>
        prev.map((o, i) => (i === current ? { ...o, progress } : o)),
      );
      if (step >= STEPS) {
        clearInterval(interval);
        setOps((prev) =>
          prev.map((o, i) =>
            i === current
              ? { ...o, status: "done", progress: 100, completedAt: new Date().toISOString() }
              : o,
          ),
        );
        if (current < ops.length - 1) {
          setTimeout(() => setCurrent((p) => p + 1), 180);
        } else {
          setAllDone(true);
          onComplete?.();
        }
      }
    }, tick);

    return () => clearInterval(interval);
  }, [current, mission.id, allDone]);

  const doneCount = ops.filter((o) => o.status === "done").length;
  const overallPct = Math.round((doneCount / ops.length) * 100);

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between mb-1">
        <div>
          <p className="mono text-xs text-white/25 uppercase tracking-wider">
            Active Mission
          </p>
          <p className="text-white/80 text-sm font-medium mt-0.5 max-w-xs truncate">
            {mission.objective}
          </p>
        </div>
        <div className="text-right">
          <span
            className={`mono text-xs px-2.5 py-1 rounded-full font-bold ${
              allDone
                ? "glass-green text-green-400"
                : "glass-amber text-amber-400"
            }`}
          >
            {doneCount}/{ops.length} OPS
          </span>
        </div>
      </div>

      {/* Global progress bar */}
      <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-200"
          style={{
            width: `${overallPct}%`,
            background: allDone
              ? "linear-gradient(90deg,#10b981,#34d399)"
              : "linear-gradient(90deg,#f59e0b,#f97316)",
          }}
        />
      </div>

      {/* Operations */}
      <div className="space-y-2 mt-2">
        {ops.map((op, i) => (
          <div
            key={op.id}
            className={`p-3.5 rounded-xl border transition-all duration-300 ${
              op.status === "done"
                ? "border-green-400/10 bg-green-400/[0.025] opacity-75"
                : op.status === "running"
                  ? "border-amber-400/25 bg-amber-400/[0.04] shadow-[0_0_24px_rgba(245,158,11,0.04)]"
                  : "border-white/[0.03] bg-white/[0.01] opacity-35"
            }`}
          >
            <div className="flex items-start gap-3">
              {/* Status indicator */}
              <div
                className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                  op.status === "done"
                    ? "bg-green-400/15"
                    : op.status === "running"
                      ? "bg-amber-400/15"
                      : "bg-white/[0.03]"
                }`}
              >
                {op.status === "done" ? (
                  <span className="text-green-400 text-xs">✓</span>
                ) : op.status === "running" ? (
                  <div className="w-2.5 h-2.5 border border-amber-400/40 border-t-amber-400 rounded-full animate-spin" />
                ) : (
                  <span className="mono text-white/15 text-xs">{i + 1}</span>
                )}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p
                    className={`text-sm leading-snug ${
                      op.status === "pending" ? "text-white/20" : "text-white/75"
                    }`}
                  >
                    {op.title}
                  </p>
                  {op.status === "done" && op.completedAt && (
                    <span className="mono text-xs text-white/15 shrink-0 whitespace-nowrap">
                      {new Date(op.completedAt).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                        second: "2-digit",
                      })}
                    </span>
                  )}
                </div>

                {/* Agent tag + output */}
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  <span
                    className="mono text-xs px-2 py-0.5 rounded-md border font-medium"
                    style={{
                      color: op.agentColor,
                      borderColor: `${op.agentColor}25`,
                      background: `${op.agentColor}0f`,
                    }}
                  >
                    {op.agent}
                  </span>
                  {op.status === "done" && op.output && (
                    <span className="text-xs text-white/20">{op.output}</span>
                  )}
                </div>

                {/* Progress bar */}
                {op.status === "running" && (
                  <div className="mt-2 h-0.5 bg-white/[0.04] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-400 rounded-full transition-all duration-100"
                      style={{ width: `${op.progress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
