"use client";
import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import { api, Message, Task, Trip, Reminder } from "@/lib/api";
import { VoiceMode } from "@/components/voice-mode";
import { OperationsBoard, buildMission, Mission } from "@/components/operations-board";
import { ObjectiveInsights } from "@/components/objective-insights";
import { ReminderSystem } from "@/components/reminder-toast";

// ─── Types ────────────────────────────────────────────────────
type OsState = "idle" | "thinking" | "executing" | "complete";
type View = "objectives" | "operations" | "trips" | "reminders" | "memory" | "agents";
type AgentNodeStatus = "idle" | "active" | "done";
interface AgentNode { id: string; label: string; x: number; y: number; status: AgentNodeStatus }
interface LogEntry  { id: string; agent: string; msg: string; color: string; ts: string }

// ─── Execution log sequence ───────────────────────────────────
const EXEC_LOG = (obj: string, intent: string) => [
  { delay:   0, agent: "System",         msg: `Objective received: "${obj.slice(0, 60)}${obj.length > 60 ? "…" : ""}"`, color: "rgba(255,255,255,0.3)" },
  { delay: 380, agent: "Intent Engine",  msg: `Classified as ${intent.toUpperCase()} · confidence 94%`,                  color: "#f59e0b" },
  { delay: 780, agent: "Memory Agent",   msg: "Scanning long-term memory for prior context…",                             color: "#34d399" },
  { delay:1150, agent: "Memory Agent",   msg: "Stored 3 new memory vectors",                                              color: "#34d399" },
  { delay:1550, agent: "Planner Agent",  msg: "Decomposing objective into executable operations…",                        color: "#818cf8" },
  { delay:2050, agent: "Planner Agent",  msg: `Generated ${intent === "travel" ? 5 : 5}-op mission roadmap`,              color: "#818cf8" },
  { delay:2500, agent: "Executor Agent", msg: "Beginning parallel operation dispatch…",                                   color: "#f59e0b" },
  { delay:3100, agent: "Database",       msg: "Writing task entities to PostgreSQL…",                                     color: "#10b981" },
  ...(intent === "travel"   ? [{ delay:3500, agent: "Database", msg: "Trip itinerary record created", color: "#10b981" }] : []),
  ...(intent === "reminder" ? [{ delay:3500, agent: "Database", msg: "Reminder scheduled in DB",     color: "#10b981" }] : []),
  { delay:4200, agent: "Memory Agent",   msg: "Objective pattern saved to long-term memory",                              color: "#34d399" },
];

// ─── Agent graph nodes & edges ────────────────────────────────
const BASE_NODES: Omit<AgentNode, "status">[] = [
  { id: "intent",   label: "INTENT",   x: 140, y: 40  },
  { id: "planner",  label: "PLANNER",  x: 140, y: 115 },
  { id: "memory",   label: "MEMORY",   x: 55,  y: 195 },
  { id: "executor", label: "EXECUTOR", x: 225, y: 195 },
  { id: "database", label: "DATABASE", x: 140, y: 275 },
];
const EDGES = [
  [140,65,140,100],[140,140,75,180],[140,140,205,180],
  [70,215,125,260],[210,215,155,260],
];

// ─── Command palette suggestions ─────────────────────────────
const SUGGESTIONS = [
  { label:"Plan a 7-day trip to Japan",       intent:"travel"   },
  { label:"Become a cybersecurity expert",     intent:"career"   },
  { label:"Launch a micro-SaaS in 30 days",    intent:"business" },
  { label:"Learn Python from scratch",         intent:"learning" },
  { label:"Lose 10kg in 3 months",             intent:"fitness"  },
  { label:"Remind me to review my OKRs",       intent:"reminder" },
  { label:"Prepare for a System Design interview", intent:"career" },
  { label:"Start an e-commerce business",      intent:"business" },
];

// ─── Agent graph SVG component ────────────────────────────────
function AgentGraph({ nodes }: { nodes: AgentNode[] }) {
  const col = (s: AgentNodeStatus) =>
    s === "active" ? { fill:"rgba(59,130,246,0.2)",  stroke:"rgba(59,130,246,0.9)",  text:"#93c5fd" }
    : s === "done" ? { fill:"rgba(16,185,129,0.15)", stroke:"rgba(16,185,129,0.8)",  text:"#34d399" }
    :                { fill:"rgba(255,255,255,0.03)", stroke:"rgba(255,255,255,0.08)", text:"rgba(255,255,255,0.2)" };

  return (
    <svg viewBox="0 0 280 320" className="w-full" style={{ maxHeight:260 }}>
      {EDGES.map(([x1,y1,x2,y2],i) => (
        <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
          stroke="rgba(255,255,255,0.06)" strokeWidth="1.5" />
      ))}
      {nodes.map((n) => {
        const c = col(n.status);
        return (
          <g key={n.id}>
            {n.status==="active" && (
              <circle cx={n.x} cy={n.y} r="32" fill="none"
                stroke={c.stroke} strokeWidth="1" opacity="0.3"
                style={{animation:"pulse-blue 1.8s infinite"}} />
            )}
            <circle cx={n.x} cy={n.y} r="26" fill={c.fill} stroke={c.stroke} strokeWidth="1.5" />
            <text x={n.x} y={n.y+4} textAnchor="middle"
              fill={c.text} fontSize="6.5"
              fontFamily="JetBrains Mono,monospace" fontWeight="700">
              {n.label}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Metrics bar ──────────────────────────────────────────────
function Metrics({ objectivesRun, tasks, trips, reminders }: {
  objectivesRun:number; tasks:Task[]; trips:Trip[]; reminders:Reminder[];
}) {
  const pending = tasks.filter(t=>t.status!=="done").length;
  const items = [
    { v:objectivesRun,     l:"MISSIONS",  c:"text-amber-400" },
    { v:tasks.length,      l:"OPERATIONS",c:"text-blue-400"  },
    { v:trips.length,      l:"TRIPS",     c:"text-violet-400"},
    { v:reminders.length,  l:"REMINDERS", c:"text-green-400" },
    { v:pending,           l:"PENDING",   c:"text-amber-400" },
  ];
  return (
    <div className="flex items-center gap-5 overflow-x-auto">
      {items.map((m) => (
        <div key={m.l} className="flex items-center gap-1.5 shrink-0">
          <span className={`mono text-base font-bold ${m.c}`}>{m.v}</span>
          <span className="mono text-xs text-white/20 uppercase tracking-wider">{m.l}</span>
        </div>
      ))}
    </div>
  );
}

// ─── Main Mission Control ────────────────────────────────────
export default function MissionControl() {
  const router                 = useRouter();
  const { token, user, clearSession } = useAuthStore();

  const [osState, setOsState]           = useState<OsState>("idle");
  const [chatId, setChatId]             = useState<string|null>(null);
  const [input, setInput]               = useState("");
  const [paletteOpen, setPaletteOpen]   = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [activeView, setActiveView]     = useState<View>("objectives");

  const [messages,  setMessages]  = useState<Message[]>([]);
  const [tasks,     setTasks]     = useState<Task[]>([]);
  const [trips,     setTrips]     = useState<Trip[]>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);

  const [logEntries,   setLogEntries]   = useState<LogEntry[]>([]);
  const [agentNodes,   setAgentNodes]   = useState<AgentNode[]>(
    BASE_NODES.map(n=>({...n,status:"idle"}))
  );
  const [currentMission, setCurrentMission] = useState<Mission|null>(null);
  const [insight, setInsight] = useState<{
    objective:string; intent:string; executionMs:number; opsCount:number;
    tasksCreated:number; tripCreated?:string; reminderCreated?:string; steps:string[];
  }|null>(null);
  const [objectivesRun, setObjectivesRun] = useState(0);
  const [execStartMs,   setExecStartMs]   = useState(0);

  const inputRef    = useRef<HTMLInputElement>(null);
  const paletteRef  = useRef<HTMLInputElement>(null);
  const logRef      = useRef<HTMLDivElement>(null);
  const scrollRef   = useRef<HTMLDivElement>(null);

  const loadData = useCallback(async (t:string) => {
    try {
      const [tt,tr,rm] = await Promise.all([
        api.listTasks(t).catch(()=>[] as Task[]),
        api.listTrips(t).catch(()=>[] as Trip[]),
        api.listReminders(t).catch(()=>[] as Reminder[]),
      ]);
      setTasks(tt); setTrips(tr); setReminders(rm);
    } catch {}
  }, []);

  useEffect(() => {
    async function initSession() {
      let activeToken = token;
      let activeUser = user;

      // Auto-guest login if no active session exists
      if (!activeToken) {
        try {
          const testEmail = "testuser_intelligence@wingman.os";
          const testPass = "SecurePassword123!";
          let tokens;
          try {
            tokens = await api.login(testEmail, testPass);
          } catch {
            await api.register(testEmail, testPass, "Autonomous User");
            tokens = await api.login(testEmail, testPass);
          }
          activeUser = await api.getMe(tokens.access_token);
          activeToken = tokens.access_token;
          useAuthStore.getState().setSession(activeToken, activeUser);
        } catch {
          router.replace("/login");
          return;
        }
      }

      if (!activeToken) return;

      try {
        const c = await api.createChat(activeToken);
        setChatId(c.id);
        loadData(activeToken);

        // Check for initialObjective passed from landing page URL
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          const initialObj = params.get("initialObjective");
          if (initialObj && c.id) {
            // Trigger automatic execution
            setTimeout(() => {
              executeObjective(initialObj);
            }, 300);
          }
        }
      } catch {}
    }

    initSession();
  }, [token, router, loadData]);

  // Ctrl+K
  useEffect(() => {
    const h = (e:KeyboardEvent) => {
      if ((e.ctrlKey||e.metaKey) && e.key==="k") {
        e.preventDefault();
        setPaletteOpen(true);
        setTimeout(()=>paletteRef.current?.focus(),40);
      }
      if (e.key==="Escape") setPaletteOpen(false);
    };
    window.addEventListener("keydown",h);
    return ()=>window.removeEventListener("keydown",h);
  }, []);

  useEffect(()=>{ logRef.current?.scrollTo({top:logRef.current.scrollHeight,behavior:"smooth"}); },[logEntries]);
  useEffect(()=>{ scrollRef.current?.scrollTo({top:scrollRef.current.scrollHeight,behavior:"smooth"}); },[messages,currentMission,insight]);

  // ── Execute objective ───────────────────────────────────────
  async function executeObjective(objective:string) {
    if (!token||!chatId||!objective.trim()||osState==="thinking"||osState==="executing") return;

    setInput("");
    setPaletteOpen(false);
    setPaletteQuery("");
    setLogEntries([]);
    setCurrentMission(null);
    setInsight(null);
    setOsState("thinking");
    setExecStartMs(Date.now());
    setAgentNodes(BASE_NODES.map(n=>({...n,status:"idle"})));

    // Optimistic user message
    const tmpId = crypto.randomUUID();
    setMessages(p=>[...p,{id:tmpId,role:"user",content:objective,agent_metadata:null,created_at:new Date().toISOString()}]);
    setActiveView("objectives");

    const apiPromise = api.sendMessage(token,chatId,objective);

    // Stream log while API runs
    let detectedIntent = "task";
    const logSeq = EXEC_LOG(objective, detectedIntent);
    logSeq.forEach(({delay,agent,msg,color})=>{
      setTimeout(()=>{
        setLogEntries(p=>[...p,{id:crypto.randomUUID(),agent,msg,color,ts:new Date().toLocaleTimeString([],{hour:"2-digit",minute:"2-digit",second:"2-digit"})}]);
        if (agent==="Intent Engine")  setAgentNodes(p=>p.map(n=>n.id==="intent"  ?{...n,status:"active"}:n));
        if (agent==="Planner Agent")  setAgentNodes(p=>p.map(n=>n.id==="intent"  ?{...n,status:"done"  }:n.id==="planner" ?{...n,status:"active"}:n));
        if (agent==="Memory Agent"&&msg.includes("Stored")) setAgentNodes(p=>p.map(n=>n.id==="memory"?{...n,status:"active"}:n));
        if (agent==="Executor Agent") setAgentNodes(p=>p.map(n=>n.id==="planner"?{...n,status:"done"  }:n.id==="executor"?{...n,status:"active"}:n));
        if (agent==="Database")       setAgentNodes(p=>p.map(n=>n.id==="executor"?{...n,status:"done" }:n.id==="database"?{...n,status:"active"}:n));
      },delay);
    });

    try {
      const reply = await apiPromise;
      detectedIntent = reply.agent_metadata?.intent ?? "task";
      const steps   = reply.agent_metadata?.steps ?? [];
      const actions = reply.agent_metadata?.actions as any ?? {};

      setOsState("executing");
      setActiveView("operations");

      const mission = buildMission(objective, detectedIntent, steps);
      setCurrentMission(mission);
      setMessages(p=>p.map(m=>m.id===tmpId?m:m).concat([reply]));

    } catch {
      setOsState("idle");
      setLogEntries(p=>[...p,{id:crypto.randomUUID(),agent:"System",msg:"⚠ Execution failed — check backend connection",color:"#ef4444",ts:new Date().toLocaleTimeString()}]);
      setAgentNodes(BASE_NODES.map(n=>({...n,status:"idle"})));
    }
  }

  function handleMissionComplete(reply:Message) {
    const steps   = reply?.agent_metadata?.steps ?? currentMission?.operations.map(o=>o.title) ?? [];
    const actions = reply?.agent_metadata?.actions as any ?? {};
    setAgentNodes(BASE_NODES.map(n=>({...n,status:"done"})));
    setOsState("complete");
    setObjectivesRun(p=>p+1);
    setInsight({
      objective:   currentMission?.objective ?? "",
      intent:      currentMission?.intent ?? "task",
      executionMs: Date.now()-execStartMs,
      opsCount:    currentMission?.operations.length ?? 5,
      tasksCreated: actions.tasks_created ?? steps.length,
      tripCreated:  actions.trip_created,
      reminderCreated: actions.reminder_created,
      steps,
    });
    if (token) loadData(token);
    setTimeout(()=>setOsState("idle"),10000);
  }

  async function toggleTask(task:Task) {
    if (!token) return;
    const next = task.status==="done"?"pending":"done";
    setTasks(p=>p.map(t=>t.id===task.id?{...t,status:next}:t));
    try { await api.updateTaskStatus(token,task.id,next); } catch { if(token) loadData(token); }
  }

  const lastReply = useMemo(()=>
    [...messages].reverse().find(m=>m.role==="assistant"),
  [messages]);

  const bgClass = osState==="thinking" ? "bg-state-thinking"
    : osState==="executing" ? "bg-state-executing"
    : osState==="complete"  ? "bg-state-complete"
    : "bg-state-idle";

  const filteredSuggestions = SUGGESTIONS.filter(s=>
    s.label.toLowerCase().includes(paletteQuery.toLowerCase())
  );
  const pendingTaskCount = tasks.filter(t=>t.status!=="done").length;

  const activeUser = user || { email: "guest@wingman.os", full_name: "Autonomous Guest", id: "guest", is_active: true };

  if (!token) {
    return (
      <div className="min-h-screen bg-[#0a0a0c] text-white flex flex-col items-center justify-center p-6 text-center">
        <div className="w-10 h-10 rounded-full border-2 border-amber-400 border-t-transparent animate-spin mb-4" />
        <p className="mono text-xs text-amber-400 uppercase tracking-widest">Initializing Wingman OS Session…</p>
      </div>
    );
  }

  return (
    <div className={`min-h-screen ${bgClass} transition-all duration-1000 flex flex-col relative overflow-hidden`}>

      {/* Ambient orbs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        {osState==="thinking"  && <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full transition-all duration-1000" style={{background:"radial-gradient(circle,rgba(59,130,246,0.09) 0%,transparent 70%)"}} />}
        {osState==="executing" && <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] rounded-full transition-all duration-1000" style={{background:"radial-gradient(circle,rgba(16,185,129,0.08) 0%,transparent 70%)"}} />}
        {osState==="complete"  && <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full transition-all duration-1000" style={{background:"radial-gradient(circle,rgba(16,185,129,0.1) 0%,transparent 60%)"}} />}
      </div>

      {/* Reminder notification system */}
      {token && <ReminderSystem reminders={reminders} onRefresh={()=>loadData(token)} />}

      {/* Command Palette */}
      {paletteOpen && (
        <div className="fixed inset-0 z-50 palette-overlay flex items-start justify-center pt-[15vh] px-4"
          onClick={e=>{ if(e.target===e.currentTarget) setPaletteOpen(false); }}>
          <div className="palette-box w-full max-w-xl animate-scale-in">
            <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.06]">
              <span className="text-white/25 text-lg">⚡</span>
              <input ref={paletteRef} value={paletteQuery}
                onChange={e=>setPaletteQuery(e.target.value)}
                onKeyDown={e=>{ if(e.key==="Enter"&&paletteQuery.trim()) executeObjective(paletteQuery.trim()); }}
                placeholder="State your objective…"
                className="flex-1 bg-transparent text-white text-base outline-none placeholder:text-white/20"
              />
              <kbd className="mono text-xs text-white/20 border border-white/[0.08] rounded px-1.5 py-0.5">ESC</kbd>
            </div>
            <div className="p-2 max-h-72 overflow-y-auto">
              {filteredSuggestions.map(s=>(
                <button key={s.label} onClick={()=>executeObjective(s.label)}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-xl hover:bg-white/[0.05] transition group text-left">
                  <span className="text-white/65 text-sm group-hover:text-white transition">{s.label}</span>
                  <span className="mono text-xs text-white/15 group-hover:text-amber-400 transition uppercase">{s.intent}</span>
                </button>
              ))}
              {paletteQuery.trim() && (
                <button onClick={()=>executeObjective(paletteQuery.trim())}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-xl glass-amber mt-1 hover:bg-amber-400/10 transition">
                  <span className="text-amber-400 text-xs mono font-bold">EXECUTE</span>
                  <span className="text-white/60 text-sm flex-1 text-left truncate">"{paletteQuery}"</span>
                  <kbd className="mono text-xs text-white/25 border border-white/[0.06] rounded px-1.5 py-0.5">↵</kbd>
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Top bar */}
      <header className="relative z-10 flex items-center justify-between px-6 py-3.5 border-b border-white/[0.05] shrink-0">
        <div className="flex items-center gap-3">
          <div className={`w-2 h-2 rounded-full transition-all duration-500 ${
            osState==="idle"      ? "status-dot-idle"
            : osState==="thinking"? "status-dot-thinking"
            : osState==="executing"?"status-dot-running"
            : "status-dot-done"
          }`} />
          <span className="mono text-xs tracking-[0.22em] text-white/30 uppercase">WINGMAN OS</span>
          <span className="mono text-xs text-white/15">·</span>
          <span className="mono text-xs text-white/25 capitalize">{osState === "idle" ? "READY" : osState === "thinking" ? "ANALYZING…" : osState === "executing" ? "EXECUTING…" : "COMPLETE"}</span>
        </div>
        <Metrics objectivesRun={objectivesRun} tasks={tasks} trips={trips} reminders={reminders} />
        <div className="flex items-center gap-2">
          <button onClick={()=>{ setPaletteOpen(true); setTimeout(()=>paletteRef.current?.focus(),40); }}
            className="glass rounded-lg px-3 py-1.5 mono text-xs text-white/30 hover:text-white/60 transition flex items-center gap-1.5">
            ⌘<span>K</span>
          </button>
          <button onClick={()=>{ clearSession(); router.push("/"); }}
            className="text-white/20 hover:text-white/45 text-xs transition mono">
            Exit OS
          </button>
        </div>
      </header>

      {/* Three-column layout */}
      <div className="relative z-10 flex-1 flex overflow-hidden min-h-0">

        {/* Left sidebar */}
        <aside className="w-56 border-r border-white/[0.05] flex flex-col shrink-0">
          <div className="flex-1 overflow-y-auto p-3 space-y-0.5">
            <p className="mono text-xs text-white/18 uppercase tracking-wider px-2 py-3">WORKSPACE</p>
            {([
              { id:"objectives", label:"Objectives", icon:"⚡", count:messages.filter(m=>m.role==="user").length },
              { id:"operations", label:"Operations", icon:"⬡",  count:pendingTaskCount  },
              { id:"trips",      label:"Trips",       icon:"✈",  count:trips.length     },
              { id:"reminders",  label:"Reminders",   icon:"◷",  count:reminders.length },
              { id:"memory",     label:"Memory",      icon:"◈",  count:0                },
              { id:"agents",     label:"Agents",      icon:"⬡",  count:0                },
            ] as const).map(item=>(
              <button key={item.id} onClick={()=>setActiveView(item.id as View)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition ${
                  activeView===item.id
                    ?"bg-white/[0.07] text-white"
                    :"text-white/35 hover:text-white/65 hover:bg-white/[0.03]"
                }`}>
                <span className="flex items-center gap-2.5">
                  <span className={activeView===item.id?"text-amber-400":"text-white/15"}>{item.icon}</span>
                  {item.label}
                </span>
                {item.count>0 && (
                  <span className={`mono text-xs px-1.5 py-0.5 rounded-full ${activeView===item.id?"bg-amber-400/15 text-amber-400":"text-white/20"}`}>
                    {item.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* System status */}
          <div className="p-3 border-t border-white/[0.04]">
            <div className="glass rounded-xl p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs text-white/25">Agent Status</span>
                <span className={`mono text-xs font-bold ${osState==="complete"?"text-green-400":osState!=="idle"?"text-amber-400":"text-white/20"}`}>
                  {osState==="idle"?"STANDBY":osState==="thinking"?"ANALYZING":osState==="executing"?"ACTIVE":"DONE"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-white/25">DB Writes</span>
                <span className="mono text-xs text-white/35">{tasks.length+trips.length+reminders.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-white/25">User</span>
                <span className="mono text-xs text-white/35 truncate max-w-[90px]">{activeUser.email.split("@")[0]}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Center — main workspace */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">

          {/* Objective input */}
          <div className="px-6 py-4 border-b border-white/[0.05] shrink-0">
            <form onSubmit={e=>{e.preventDefault(); executeObjective(input)}} className="flex items-center gap-2.5">
              <div className={`w-2 h-2 rounded-full shrink-0 transition-all duration-500 ${
                osState!=="idle"?"status-dot-running":"status-dot-idle"
              }`} />
              <input ref={inputRef} value={input} onChange={e=>setInput(e.target.value)}
                placeholder="What would you like Wingman to accomplish?   (or press ⌘K)"
                disabled={osState==="thinking"||osState==="executing"}
                className="input-os flex-1 px-4 py-3 text-[15px]"
              />
              <VoiceMode onTranscript={executeObjective} disabled={osState==="thinking"||osState==="executing"} />
              <button type="submit"
                disabled={!input.trim()||osState==="thinking"||osState==="executing"}
                className="btn-primary px-5 py-3 text-sm rounded-xl shrink-0 disabled:opacity-35">
                {osState==="thinking"||osState==="executing"?"Running…":"Execute →"}
              </button>
            </form>
          </div>

          {/* Execution log */}
          {logEntries.length>0 && (
            <div className="px-6 pt-4 shrink-0">
              <div className="glass rounded-xl p-4 max-h-44 overflow-y-auto" ref={logRef}>
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-1.5 h-1.5 rounded-full ${osState==="complete"?"bg-green-400":"bg-amber-400 animate-pulse"}`} />
                  <span className="mono text-xs text-white/25 uppercase tracking-wider">Execution Log</span>
                </div>
                <div className="space-y-1">
                  {logEntries.map(entry=>(
                    <div key={entry.id} className="log-line flex items-start gap-2.5 text-xs">
                      <span className="mono text-white/20 shrink-0 w-16">{entry.ts}</span>
                      <span className="mono font-bold shrink-0 w-24" style={{color:entry.color}}>{entry.agent}</span>
                      <span className="text-white/45 leading-relaxed">{entry.msg}</span>
                    </div>
                  ))}
                  {(osState==="thinking"||osState==="executing") && (
                    <div className="flex items-center gap-2 pl-40">
                      <span className="mono text-xs text-white/20 animate-pulse">processing</span>
                      <span className="cursor-blink text-amber-400">▊</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Content area */}
          <div className="flex-1 overflow-y-auto p-6" ref={scrollRef}>

            {/* OBJECTIVES VIEW */}
            {activeView==="objectives" && (
              <div className="space-y-4">
                {messages.length===0 && osState==="idle" && (
                  <div className="text-center py-16">
                    <div className="w-16 h-16 rounded-2xl glass flex items-center justify-center text-3xl mx-auto mb-5 animate-float">⚡</div>
                    <h2 className="text-2xl font-bold text-white mb-2">Mission Control</h2>
                    <p className="text-white/30 text-sm max-w-xs mx-auto mb-10 leading-relaxed">
                      State any objective. Wingman decomposes, assigns agents, executes operations, and persists results.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-w-lg mx-auto">
                      {SUGGESTIONS.slice(0,6).map(s=>(
                        <button key={s.label} onClick={()=>executeObjective(s.label)}
                          className="glass text-left px-4 py-3.5 rounded-xl hover:border-amber-400/25 transition group">
                          <p className="text-white/60 text-sm group-hover:text-white transition">{s.label}</p>
                          <p className="mono text-xs text-white/15 uppercase mt-1 group-hover:text-amber-400 transition">{s.intent}</p>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {messages.filter(m=>m.role==="user").map((userMsg,idx)=>{
                  const assistantMsg = messages.find((m,i)=>m.role==="assistant"&&i>messages.indexOf(userMsg));
                  const plan = assistantMsg?.agent_metadata;
                  return (
                    <div key={userMsg.id} className="animate-fade-up glass rounded-2xl p-5 border border-white/[0.05]">
                      <div className="flex items-start gap-3 mb-4 pb-4 border-b border-white/[0.04]">
                        <div className="w-8 h-8 rounded-xl bg-amber-400/10 border border-amber-400/15 flex items-center justify-center shrink-0">
                          <span className="text-amber-400 text-sm">⚡</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="mono text-xs text-white/20 uppercase tracking-wider mb-1">Mission {idx+1}</p>
                          <p className="text-white font-medium">{userMsg.content}</p>
                        </div>
                        {plan && (
                          <span className="mono text-xs px-2.5 py-1.5 rounded-full glass-amber text-amber-400 font-bold uppercase shrink-0">
                            {plan.intent}
                          </span>
                        )}
                      </div>
                      {plan?.steps && (
                        <div className="space-y-2 mb-4">
                          {plan.steps.map((step:string,i:number)=>(
                            <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/[0.03]">
                              <span className="mono text-xs text-amber-400 font-bold w-6 text-center">{String(i+1).padStart(2,"0")}</span>
                              <span className="text-white/60 text-xs">{step}</span>
                            </div>
                          ))}
                        </div>
                      )}
                      {(plan?.actions as any) && (
                        <div className="flex flex-wrap gap-2">
                          {(plan.actions as any).tasks_created && <span className="glass-green mono text-xs px-3 py-1.5 rounded-full text-green-400">☐ {(plan.actions as any).tasks_created} ops in DB</span>}
                          {(plan.actions as any).trip_created    && <span className="glass-blue mono text-xs px-3 py-1.5 rounded-full text-blue-400">✈ Trip created</span>}
                          {(plan.actions as any).reminder_created && <span className="mono text-xs px-3 py-1.5 rounded-full text-violet-400 border border-violet-400/20 bg-violet-400/[0.05]">◷ Reminder set</span>}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* OPERATIONS VIEW */}
            {activeView==="operations" && (
              <div className="space-y-5">
                {currentMission && (
                  <OperationsBoard
                    mission={currentMission}
                    onComplete={()=>{
                      const reply = messages.find(m=>m.role==="assistant"&&messages.indexOf(m)===messages.length-1);
                      handleMissionComplete(reply as Message);
                    }}
                  />
                )}
                {insight && (
                  <ObjectiveInsights
                    data={insight}
                    onClose={()=>setInsight(null)}
                    onNextObjective={(obj)=>{ setActiveView("objectives"); executeObjective(obj); }}
                  />
                )}
                {!currentMission && tasks.length===0 && (
                  <div className="text-center py-16 glass rounded-2xl border border-white/[0.04]">
                    <p className="text-white/25 text-sm">No operations yet. Execute an objective to generate them automatically.</p>
                  </div>
                )}
                {!currentMission && tasks.length>0 && (
                  <div className="space-y-2">
                    <p className="mono text-xs text-white/25 uppercase tracking-wider mb-4">Operations from DB</p>
                    {tasks.map(task=>(
                      <div key={task.id} onClick={()=>toggleTask(task)}
                        className={`flex items-center justify-between p-4 rounded-xl border transition cursor-pointer ${
                          task.status==="done"
                            ?"border-white/[0.03] bg-white/[0.01] opacity-50"
                            :"glass border-white/[0.05] hover:border-amber-400/25"
                        }`}>
                        <div className="flex items-center gap-3">
                          <div className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition ${task.status==="done"?"border-green-400 bg-green-400/15":"border-white/15"}`}>
                            {task.status==="done" && <span className="text-green-400 text-xs">✓</span>}
                          </div>
                          <p className={`text-sm ${task.status==="done"?"text-white/25 line-through":"text-white/70"}`}>{task.title}</p>
                        </div>
                        <span className={`mono text-xs px-2.5 py-1 rounded-full font-bold ${task.status==="done"?"text-green-400/60 bg-green-400/[0.04]":"text-amber-400 bg-amber-400/[0.08]"}`}>
                          {task.status==="done"?"DONE":"PENDING"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* TRIPS VIEW */}
            {activeView==="trips" && (
              <div>
                <h2 className="text-xl font-bold text-white mb-5">Travel Itineraries</h2>
                {trips.length===0 ? (
                  <div className="text-center py-16 glass rounded-2xl border border-white/[0.04]">
                    <p className="text-white/25 text-sm">No trips yet. Try: "Plan my trip to Tokyo"</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {trips.map(trip=>(
                      <div key={trip.id} className="glass rounded-2xl p-5 border border-white/[0.05] hover:border-blue-400/25 transition">
                        <div className="flex items-center gap-2 mb-3">
                          <span>✈</span>
                          <span className="mono text-xs px-2 py-0.5 rounded-full bg-blue-400/10 text-blue-400 uppercase">{trip.status}</span>
                        </div>
                        <h3 className="text-white font-semibold">{trip.destination}</h3>
                        <p className="text-white/20 text-xs mono mt-1">Stored · Ready for planning</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* REMINDERS VIEW */}
            {activeView==="reminders" && (
              <div>
                <h2 className="text-xl font-bold text-white mb-5">Scheduled Reminders</h2>
                {reminders.length===0 ? (
                  <div className="text-center py-16 glass rounded-2xl border border-white/[0.04]">
                    <p className="text-white/25 text-sm">No reminders. Try: "Remind me to review my goals tomorrow"</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {reminders.map(r=>(
                      <div key={r.id} className="glass rounded-xl p-4 border border-white/[0.05] flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-violet-400">◷</span>
                          <div>
                            <p className="text-white/75 text-sm">{r.title}</p>
                            <p className="mono text-xs text-white/25 mt-0.5">{new Date(r.remind_at).toLocaleString()}</p>
                          </div>
                        </div>
                        <span className="mono text-xs text-violet-400 bg-violet-400/10 px-2.5 py-1 rounded-full">
                          {r.is_sent?"SENT":"ACTIVE"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* MEMORY VIEW */}
            {activeView==="memory" && (
              <div className="text-center py-10">
                <p className="mono text-xs text-white/25 uppercase mb-6">AI Long-Term Memory</p>
                <a href="/memory" className="btn-primary px-6 py-3 rounded-xl text-sm inline-block">
                  Open Knowledge Graph →
                </a>
              </div>
            )}

            {/* AGENTS VIEW */}
            {activeView==="agents" && (
              <div className="text-center py-10">
                <p className="mono text-xs text-white/25 uppercase mb-6">Agent Health Dashboard</p>
                <a href="/agents" className="btn-primary px-6 py-3 rounded-xl text-sm inline-block">
                  Open Agent Panel →
                </a>
              </div>
            )}
          </div>
        </main>

        {/* Right rail — AI Brain */}
        <aside className="w-64 border-l border-white/[0.05] p-5 hidden lg:flex flex-col shrink-0">
          <p className="mono text-xs text-white/20 uppercase tracking-wider mb-4">AI BRAIN</p>

          {(osState!=="idle") ? (
            <div className="space-y-5">
              <AgentGraph nodes={agentNodes} />
              <div className="space-y-2">
                {agentNodes.map(n=>(
                  <div key={n.id} className="flex items-center justify-between text-xs">
                    <span className="mono text-white/30 uppercase">{n.label}</span>
                    <span className={`mono font-bold ${n.status==="done"?"text-green-400":n.status==="active"?"text-amber-400":"text-white/15"}`}>
                      {n.status==="done"?"DONE":n.status==="active"?"ACTIVE":"STANDBY"}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="text-center py-8 border border-dashed border-white/[0.05] rounded-xl">
                <p className="text-white/20 text-xs">Agents standing by.</p>
                <p className="text-white/12 text-xs mt-1">Submit an objective to activate.</p>
              </div>
              {/* Quick stats */}
              <div className="space-y-2">
                {[
                  {l:"Last objective", v:messages.filter(m=>m.role==="user").length>0?messages.filter(m=>m.role==="user").slice(-1)[0].content.slice(0,25)+"…":"None yet"},
                  {l:"Operations run", v:String(tasks.length)},
                  {l:"Memory entries", v:String(tasks.length+trips.length+reminders.length)},
                ].map(s=>(
                  <div key={s.l} className="glass rounded-xl p-3">
                    <p className="mono text-xs text-white/20">{s.l}</p>
                    <p className="text-white/60 text-xs mt-1 truncate">{s.v}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
