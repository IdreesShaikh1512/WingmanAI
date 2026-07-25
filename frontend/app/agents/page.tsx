"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import Link from "next/link";

interface AgentDef {
  id: string;
  name: string;
  role: string;
  color: string;
  icon: string;
  healthBase: number;
  latencyBase: number;
}

const AGENTS: AgentDef[] = [
  { id:"intent",   name:"Intent Engine",  role:"Objective classification & NLP",  color:"#f59e0b", icon:"⚡", healthBase:98, latencyBase:45  },
  { id:"planner",  name:"Planner Agent",  role:"Mission decomposition & roadmap",  color:"#818cf8", icon:"◈",  healthBase:96, latencyBase:120 },
  { id:"memory",   name:"Memory Agent",   role:"Long-term storage & retrieval",    color:"#34d399", icon:"◷",  healthBase:99, latencyBase:30  },
  { id:"executor", name:"Executor Agent", role:"Parallel operation dispatch",      color:"#f59e0b", icon:"⬡",  healthBase:94, latencyBase:200 },
  { id:"database", name:"Database Agent", role:"PostgreSQL writes & reads",        color:"#10b981", icon:"☐",  healthBase:100,latencyBase:25  },
  { id:"calendar", name:"Calendar Agent", role:"Event scheduling & reminders",    color:"#f472b6", icon:"◑",  healthBase:97, latencyBase:60  },
];

const OPS_HISTORY = [
  "Classified: TRAVEL (94%)",
  "Generated 5-op roadmap",
  "Written task entities",
  "Scanned memory store",
  "Created trip record",
  "Stored 3 memory vectors",
  "Dispatched sub-operations",
];

export default function AgentsPage() {
  const router = useRouter();
  const { token } = useAuthStore();
  const [latencies, setLatencies] = useState<Record<string,number>>({});
  const [healths,   setHealths]   = useState<Record<string,number>>({});
  const [queues,    setQueues]    = useState<Record<string,number>>({});
  const [tokens,    setTokens]    = useState<Record<string,number>>({});
  const [lastOp,    setLastOp]    = useState<Record<string,string>>({});
  const [activeId,  setActiveId]  = useState<string|null>(null);

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
    // Initialize values
    const l:Record<string,number>={}, h:Record<string,number>={}, q:Record<string,number>={}, t:Record<string,number>={}, lo:Record<string,string>={};
    AGENTS.forEach(a=>{
      l[a.id]=a.latencyBase+Math.floor(Math.random()*30);
      h[a.id]=a.healthBase;
      q[a.id]=Math.floor(Math.random()*3);
      t[a.id]=Math.floor(Math.random()*1800)+200;
      lo[a.id]=OPS_HISTORY[Math.floor(Math.random()*OPS_HISTORY.length)];
    });
    setLatencies(l); setHealths(h); setQueues(q); setTokens(t); setLastOp(lo);
  }, [token, router]);

  // Simulate live fluctuation
  useEffect(() => {
    const interval = setInterval(()=>{
      setLatencies(prev=>{
        const next={...prev};
        const a=AGENTS[Math.floor(Math.random()*AGENTS.length)];
        next[a.id]=Math.max(10,a.latencyBase+Math.floor((Math.random()-0.5)*60));
        return next;
      });
      setQueues(prev=>{
        const next={...prev};
        const a=AGENTS[Math.floor(Math.random()*AGENTS.length)];
        next[a.id]=Math.floor(Math.random()*5);
        return next;
      });
      setTokens(prev=>{
        const next={...prev};
        AGENTS.forEach(a=>{next[a.id]=(next[a.id]??0)+Math.floor(Math.random()*50);});
        return next;
      });
      // Occasionally update last op
      if (Math.random()>0.6) {
        const a=AGENTS[Math.floor(Math.random()*AGENTS.length)];
        setLastOp(prev=>({...prev,[a.id]:OPS_HISTORY[Math.floor(Math.random()*OPS_HISTORY.length)]}));
        setActiveId(a.id);
        setTimeout(()=>setActiveId(null),800);
      }
    },2000);
    return ()=>clearInterval(interval);
  },[]);

  const total = {
    health: Math.round(AGENTS.reduce((s,a)=>(s+(healths[a.id]??100)),0)/AGENTS.length),
    latency: Math.round(AGENTS.reduce((s,a)=>(s+(latencies[a.id]??100)),0)/AGENTS.length),
    queue: AGENTS.reduce((s,a)=>(s+(queues[a.id]??0)),0),
    tokens: Object.values(tokens).reduce((s,v)=>s+v,0),
  };

  return (
    <div className="min-h-screen bg-state-idle flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/[0.05]">
        <div className="flex items-center gap-3">
          <Link href="/mission-control" className="text-white/25 hover:text-white/60 transition mono text-xs">← OS</Link>
          <span className="text-white/15">·</span>
          <span className="mono text-xs tracking-[0.2em] text-white/35 uppercase">AI Agent Network</span>
          <span className="flex items-center gap-1 ml-2">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            <span className="mono text-xs text-green-400">LIVE</span>
          </span>
        </div>
        <div className="flex items-center gap-6">
          {[
            { label:"SYSTEM HEALTH", value:`${total.health}%`,   color:"text-green-400" },
            { label:"AVG LATENCY",   value:`${total.latency}ms`, color:"text-amber-400" },
            { label:"QUEUE DEPTH",   value:String(total.queue),  color:"text-blue-400"  },
            { label:"TOKENS/SESSION",value:`${(total.tokens/1000).toFixed(1)}K`, color:"text-violet-400" },
          ].map(m=>(
            <div key={m.label} className="text-right">
              <p className={`mono text-sm font-bold ${m.color}`}>{m.value}</p>
              <p className="mono text-xs text-white/20 uppercase">{m.label}</p>
            </div>
          ))}
        </div>
      </header>

      <div className="flex-1 p-6 overflow-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {AGENTS.map(agent=>{
            const lat  = latencies[agent.id] ?? agent.latencyBase;
            const hlth = healths[agent.id]   ?? agent.healthBase;
            const q    = queues[agent.id]    ?? 0;
            const tok  = tokens[agent.id]    ?? 0;
            const op   = lastOp[agent.id]    ?? "Standby";
            const isActive = activeId===agent.id;

            return (
              <div key={agent.id}
                className={`glass rounded-2xl p-5 border transition-all duration-300 ${
                  isActive
                    ?"border-amber-400/30 shadow-[0_0_30px_rgba(245,158,11,0.06)]"
                    :"border-white/[0.05] hover:border-white/[0.1]"
                }`}>
                {/* Agent header */}
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                      style={{background:`${agent.color}12`,border:`1px solid ${agent.color}25`}}>
                      {agent.icon}
                    </div>
                    <div>
                      <p className="font-semibold text-white text-sm">{agent.name}</p>
                      <p className="text-white/30 text-xs mt-0.5">{agent.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className={`w-2 h-2 rounded-full ${isActive?"animate-pulse-amber bg-amber-400":"bg-green-400"}`}
                      style={{boxShadow:isActive?`0 0 8px ${agent.color}`:"none"}} />
                    <span className="mono text-xs" style={{color:isActive?agent.color:"rgba(52,211,153,0.8)"}}>
                      {isActive?"ACTIVE":"READY"}
                    </span>
                  </div>
                </div>

                {/* Health bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="mono text-xs text-white/25 uppercase">Health</span>
                    <span className="mono text-xs font-bold" style={{color:hlth>90?"#4ade80":hlth>70?"#f59e0b":"#ef4444"}}>
                      {hlth}%
                    </span>
                  </div>
                  <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all duration-500"
                      style={{
                        width:`${hlth}%`,
                        background:hlth>90?"linear-gradient(90deg,#10b981,#4ade80)":hlth>70?"#f59e0b":"#ef4444"
                      }} />
                  </div>
                </div>

                {/* Metrics grid */}
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {[
                    { label:"Latency",  value:`${lat}ms`,            color:"text-amber-400"  },
                    { label:"Queue",    value:`${q} ops`,             color:"text-blue-400"   },
                    { label:"Tokens",   value:`${(tok/1000).toFixed(1)}K`,color:"text-violet-400"},
                    { label:"Uptime",   value:"99.9%",                color:"text-green-400"  },
                  ].map(m=>(
                    <div key={m.label} className="bg-white/[0.025] rounded-xl p-3 border border-white/[0.03]">
                      <p className="mono text-xs text-white/20 uppercase">{m.label}</p>
                      <p className={`mono text-sm font-bold mt-1 ${m.color}`}>{m.value}</p>
                    </div>
                  ))}
                </div>

                {/* Last operation */}
                <div className="glass rounded-xl px-3 py-2.5 flex items-center gap-2.5">
                  {isActive && <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse shrink-0" />}
                  <p className={`text-xs leading-relaxed ${isActive?"text-amber-400":"text-white/30"}`}>{op}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
