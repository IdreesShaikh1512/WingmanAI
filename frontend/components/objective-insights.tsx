"use client";

interface InsightData {
  objective: string;
  intent: string;
  executionMs: number;
  opsCount: number;
  tasksCreated: number;
  tripCreated?: string;
  reminderCreated?: string;
  steps: string[];
}

const RECOMMENDATIONS: Record<string, string[]> = {
  travel:   ["Book flights 6–8 weeks ahead for best pricing", "Apply for travel insurance before departure", "Download offline maps and currency converter"],
  learning: ["Dedicate a consistent 1-hour block daily over irregular long sessions", "Use spaced repetition for memorization (Anki, SuperMemo)", "Teach the concept to someone else to surface gaps"],
  career:   ["Join Discord / Reddit / LinkedIn communities in your target domain", "Contribute to open source for portfolio proof-of-work", "Cold-email 3 people already doing your target role this week"],
  business: ["Talk to 10 potential customers BEFORE writing code", "Start with a no-code MVP to validate demand fast", "Define and track one north-star metric from day one"],
  fitness:  ["Consistency at 70% effort beats intensity at 100% 3×/week", "Track sleep quality — it drives 80% of recovery", "Take weekly progress photos: visual data motivates better than scale numbers"],
  reminder: ["Enable browser notifications for real-time reminder delivery", "Create backup reminders 30 min before critical deadlines", "Review all active reminders every Sunday"],
  task:     ["Timebox each sub-task to prevent scope creep", "Do the hardest item first thing — decision fatigue is real", "Ship partial wins: momentum compounds"],
  general:  ["Document progress weekly for self-accountability", "Set a strict scope boundary before starting", "Schedule a 48-hour review checkpoint after initial execution"],
};

const NEXT_OBJECTIVES: Record<string, string[]> = {
  travel:   ["Book accommodation for the first 3 nights", "Build a day-by-day packing checklist", "Research local cuisine and dietary options"],
  learning: ["Find 3 practice exercises to stress-test your knowledge", "Build one small project applying the concepts", "Schedule a peer code/work review session"],
  career:   ["Update your LinkedIn profile with new skills", "Create a 90-day certification study schedule", "Complete one CTF or hands-on lab challenge this week"],
  business: ["Define your ideal customer profile (ICP) in one paragraph", "Create a 30-day launch timeline with daily milestones", "Identify top 3 paid acquisition channels to test"],
  fitness:  ["Schedule your first 3 training sessions in your calendar", "Meal prep for the first 3 days", "Record your baseline measurements and photos"],
  reminder: ["Set a recurring weekly reminder to review active goals", "Create a task to prepare 24 hours before the reminder fires", "Add a backup reminder 1 hour before as a safety net"],
  task:     ["Break Step 1 into 3 smaller sub-tasks", "Assign a hard deadline for the overall objective", "Schedule a weekly check-in to track progress"],
  general:  ["Define success criteria with measurable outcomes", "Set a 7-day checkpoint to evaluate early results", "Identify potential blockers and contingency plans"],
};

interface ObjectiveInsightsProps {
  data: InsightData;
  onClose: () => void;
  onNextObjective?: (obj: string) => void;
}

export function ObjectiveInsights({ data, onClose, onNextObjective }: ObjectiveInsightsProps) {
  const recs    = RECOMMENDATIONS[data.intent]  ?? RECOMMENDATIONS.general;
  const nextObjs = NEXT_OBJECTIVES[data.intent] ?? NEXT_OBJECTIVES.general;
  const execSec  = (data.executionMs / 1000).toFixed(1);

  return (
    <div className="animate-fade-up glass rounded-2xl border border-green-400/15 p-5 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-green-400/10 border border-green-400/20 flex items-center justify-center shrink-0">
            <span className="text-green-400">✓</span>
          </div>
          <div>
            <p className="mono text-xs text-green-400 font-bold uppercase tracking-wider">
              Mission Complete
            </p>
            <p className="text-white/60 text-sm mt-0.5 max-w-xs">{data.objective}</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white/20 hover:text-white/60 transition text-xl leading-none shrink-0"
          aria-label="Close insights"
        >
          ×
        </button>
      </div>

      {/* Execution metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {[
          { label: "Exec Time", value: `${execSec}s` },
          { label: "Operations", value: data.opsCount },
          { label: "DB Writes", value: data.tasksCreated + (data.tripCreated ? 1 : 0) + (data.reminderCreated ? 1 : 0) },
          { label: "Intent", value: data.intent.toUpperCase() },
        ].map((m) => (
          <div key={m.label} className="bg-white/[0.025] rounded-xl p-3 border border-white/[0.04]">
            <p className="mono text-xs text-white/25 uppercase">{m.label}</p>
            <p className="text-white font-bold mt-1 text-sm">{m.value}</p>
          </div>
        ))}
      </div>

      {/* Artifacts created */}
      <div className="flex flex-wrap gap-2">
        {data.tasksCreated > 0 && (
          <span className="glass-green mono text-xs px-3 py-1.5 rounded-full text-green-400 font-medium">
            ☐ {data.tasksCreated} tasks in DB
          </span>
        )}
        {data.tripCreated && (
          <span className="glass-blue mono text-xs px-3 py-1.5 rounded-full text-blue-400 font-medium">
            ✈ Trip itinerary created
          </span>
        )}
        {data.reminderCreated && (
          <span className="mono text-xs px-3 py-1.5 rounded-full text-violet-400 font-medium border border-violet-400/20 bg-violet-400/[0.06]">
            ◷ Reminder scheduled
          </span>
        )}
      </div>

      {/* AI Recommendations */}
      <div>
        <p className="mono text-xs text-white/25 uppercase tracking-wider mb-2.5">
          AI Recommendations
        </p>
        <div className="space-y-2">
          {recs.map((r, i) => (
            <div key={i} className="flex items-start gap-2.5 text-xs text-white/45">
              <span className="text-amber-400 shrink-0 mt-px">→</span>
              <span className="leading-relaxed">{r}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Suggested next objectives */}
      <div>
        <p className="mono text-xs text-white/25 uppercase tracking-wider mb-2.5">
          Suggested Next Objectives
        </p>
        <div className="space-y-1.5">
          {nextObjs.map((obj, i) => (
            <button
              key={i}
              onClick={() => onNextObjective?.(obj)}
              className="w-full text-left text-xs text-white/45 hover:text-amber-400 px-3 py-2.5 glass rounded-xl transition flex items-center gap-2.5 group"
            >
              <span className="text-amber-400/25 group-hover:text-amber-400 transition shrink-0">⚡</span>
              <span>{obj}</span>
              <span className="ml-auto text-white/10 group-hover:text-amber-400/40 transition shrink-0">→</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
