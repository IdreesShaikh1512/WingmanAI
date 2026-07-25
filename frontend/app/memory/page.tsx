"use client";
import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import Link from "next/link";

// ─── Knowledge Graph Data ─────────────────────────────────────
interface MemNode {
  id: string;
  label: string;
  group: string;
  color: string;
  x: number;
  y: number;
  r: number;
  detail?: string;
}

interface MemEdge {
  source: string;
  target: string;
}

const BASE_NODES: MemNode[] = [
  // User center
  { id:"user",     label:"YOU",        group:"center",  color:"#f59e0b", x:380, y:250, r:32, detail:"Your personal AI memory hub" },
  // Categories
  { id:"travel",   label:"Travel",     group:"cat",     color:"#60a5fa", x:220, y:110, r:24, detail:"Destinations visited and planned" },
  { id:"career",   label:"Career",     group:"cat",     color:"#818cf8", x:550, y:110, r:24, detail:"Skills, certifications, learning goals" },
  { id:"business", label:"Business",   group:"cat",     color:"#fb923c", x:560, y:390, r:24, detail:"Projects, ventures, strategies" },
  { id:"fitness",  label:"Fitness",    group:"cat",     color:"#4ade80", x:220, y:390, r:24, detail:"Health goals and workout history" },
  { id:"prefs",    label:"Preferences",group:"cat",     color:"#f472b6", x:380, y:70,  r:20, detail:"Airlines, hotels, food, budget" },
  // Sub-nodes - Travel
  { id:"japan",    label:"Japan",      group:"travel",  color:"#93c5fd", x:130, y:60,  r:16, detail:"Trip planned for next month" },
  { id:"paris",    label:"Paris",      group:"travel",  color:"#93c5fd", x:90,  y:155, r:16, detail:"Dream destination" },
  { id:"goa",      label:"Goa",        group:"travel",  color:"#93c5fd", x:165, y:185, r:14, detail:"Upcoming trip" },
  // Sub-nodes - Career
  { id:"cyber",    label:"CyberSec",   group:"career",  color:"#a5b4fc", x:665, y:65,  r:16, detail:"Learning path in progress" },
  { id:"python",   label:"Python",     group:"career",  color:"#a5b4fc", x:650, y:165, r:16, detail:"Intermediate level" },
  { id:"sql",      label:"SQL",        group:"career",  color:"#a5b4fc", x:580, y:200, r:14, detail:"Interview prep" },
  // Sub-nodes - Business
  { id:"saas",     label:"SaaS MVP",   group:"business",color:"#fed7aa", x:660, y:370, r:16, detail:"30-day launch plan" },
  { id:"content",  label:"Content",    group:"business",color:"#fed7aa", x:650, y:450, r:14, detail:"Content marketing strategy" },
  // Sub-nodes - Fitness
  { id:"weightloss",label:"Weight",    group:"fitness", color:"#bbf7d0", x:130, y:450, r:14, detail:"10kg goal in 3 months" },
  { id:"running",   label:"Running",   group:"fitness", color:"#bbf7d0", x:155, y:340, r:13, detail:"5km baseline set" },
  // Preferences
  { id:"emirates",  label:"Emirates",  group:"prefs",   color:"#f9a8d4", x:300, y:30,  r:13, detail:"Preferred airline" },
  { id:"budget",    label:"Budget",    group:"prefs",   color:"#f9a8d4", x:465, y:35,  r:13, detail:"Mid-range traveler" },
];

const BASE_EDGES: MemEdge[] = [
  {source:"user",target:"travel"},
  {source:"user",target:"career"},
  {source:"user",target:"business"},
  {source:"user",target:"fitness"},
  {source:"user",target:"prefs"},
  {source:"travel",target:"japan"},
  {source:"travel",target:"paris"},
  {source:"travel",target:"goa"},
  {source:"career",target:"cyber"},
  {source:"career",target:"python"},
  {source:"career",target:"sql"},
  {source:"business",target:"saas"},
  {source:"business",target:"content"},
  {source:"fitness",target:"weightloss"},
  {source:"fitness",target:"running"},
  {source:"prefs",target:"emirates"},
  {source:"prefs",target:"budget"},
];

const MEMORY_ENTRIES = [
  { cat:"Travel",   key:"Preferred airline",    val:"Emirates (economy)",  icon:"✈" },
  { cat:"Travel",   key:"Budget range",         val:"$1,500–$3,000 / trip", icon:"💰" },
  { cat:"Travel",   key:"Food preference",      val:"Vegetarian-friendly",  icon:"🥗" },
  { cat:"Career",   key:"Primary skill",        val:"Backend engineering",  icon:"💻" },
  { cat:"Career",   key:"Learning goal",        val:"Cybersecurity (2024)", icon:"🎯" },
  { cat:"Business", key:"Work style",           val:"Remote, async-first",  icon:"⚡" },
  { cat:"Business", key:"Active project",       val:"SaaS MVP (30-day)",    icon:"🚀" },
  { cat:"Fitness",  key:"Goal",                 val:"Lose 10kg in 3 months",icon:"💪" },
  { cat:"Fitness",  key:"Preferred workout",    val:"Morning runs 5–7am",   icon:"🏃" },
];

export default function MemoryPage() {
  const router = useRouter();
  const { token } = useAuthStore();
  const [selectedNode, setSelectedNode] = useState<MemNode|null>(null);
  const [hoveredNode,  setHoveredNode]  = useState<string|null>(null);
  const [searchQuery,  setSearchQuery]  = useState("");
  const [activeFilter, setActiveFilter] = useState("All");
  const [pulse, setPulse] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!token) { router.replace("/login"); return; }
  }, [token, router]);

  // Pulse random nodes
  useEffect(() => {
    const interval = setInterval(() => {
      const candidates = BASE_NODES.filter(n=>n.group!=="center");
      const pick = candidates[Math.floor(Math.random()*candidates.length)];
      setPulse(prev=>new Set([...prev,pick.id]));
      setTimeout(()=>setPulse(prev=>{const s=new Set(prev);s.delete(pick.id);return s;}),1200);
    },2500);
    return ()=>clearInterval(interval);
  },[]);

  const nodeById = useMemo(()=>Object.fromEntries(BASE_NODES.map(n=>[n.id,n])),[] );

  const filteredMemory = useMemo(()=>
    MEMORY_ENTRIES.filter(e=>{
      const matchCat = activeFilter==="All"||e.cat===activeFilter;
      const matchQ   = !searchQuery||(e.key+e.val).toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat&&matchQ;
    }),
  [activeFilter, searchQuery]);

  const categories = ["All","Travel","Career","Business","Fitness"];

  return (
    <div className="min-h-screen bg-state-idle flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/[0.05]">
        <div className="flex items-center gap-3">
          <Link href="/mission-control" className="text-white/25 hover:text-white/60 transition mono text-xs">← OS</Link>
          <span className="text-white/15">·</span>
          <span className="mono text-xs tracking-[0.2em] text-white/35 uppercase">AI Memory · Knowledge Graph</span>
        </div>
        <div className="flex items-center gap-2">
          <input value={searchQuery} onChange={e=>setSearchQuery(e.target.value)}
            placeholder="Search memory…"
            className="input-os px-4 py-2 text-sm w-52" />
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden min-h-0">
        {/* Graph */}
        <div className="flex-1 relative overflow-hidden">
          <svg viewBox="0 0 760 500" className="w-full h-full">
            {/* Edges */}
            {BASE_EDGES.map((e,i)=>{
              const s=nodeById[e.source], t=nodeById[e.target];
              if(!s||!t) return null;
              const isHighlighted = hoveredNode===e.source||hoveredNode===e.target||selectedNode?.id===e.source||selectedNode?.id===e.target;
              return (
                <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  stroke={isHighlighted?"rgba(245,158,11,0.4)":"rgba(255,255,255,0.05)"}
                  strokeWidth={isHighlighted?"1.5":"1"}
                  style={{transition:"all 0.3s ease"}} />
              );
            })}

            {/* Nodes */}
            {BASE_NODES.map(n=>{
              const isSelected = selectedNode?.id===n.id;
              const isHovered  = hoveredNode===n.id;
              const isPulse    = pulse.has(n.id);
              const opacity    = hoveredNode&&!isHovered&&!isSelected?0.3:1;
              return (
                <g key={n.id} style={{cursor:"pointer",opacity,transition:"opacity 0.2s"}}
                  onClick={()=>setSelectedNode(isSelected?null:n)}
                  onMouseEnter={()=>setHoveredNode(n.id)}
                  onMouseLeave={()=>setHoveredNode(null)}>
                  {/* Pulse ring */}
                  {isPulse && (
                    <circle cx={n.x} cy={n.y} r={n.r+12} fill="none"
                      stroke={n.color} strokeWidth="1" opacity="0.4"
                      style={{animation:"pulse-amber 1s ease-out"}} />
                  )}
                  {/* Selection ring */}
                  {(isSelected||isHovered) && (
                    <circle cx={n.x} cy={n.y} r={n.r+6} fill="none"
                      stroke={n.color} strokeWidth="1.5" opacity="0.5" />
                  )}
                  {/* Node circle */}
                  <circle cx={n.x} cy={n.y} r={n.r}
                    fill={`${n.color}18`}
                    stroke={n.color}
                    strokeWidth={isSelected?"2":isHovered?"1.8":"1.2"}
                    style={{transition:"all 0.2s ease"}} />
                  {/* Label */}
                  <text x={n.x} y={n.y+(n.r>20?4:3)} textAnchor="middle"
                    fill={n.color} fontSize={n.r>20?"9":"7"}
                    fontFamily="JetBrains Mono,monospace" fontWeight="700">
                    {n.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Selected node detail */}
          {selectedNode && (
            <div className="absolute bottom-6 left-6 glass rounded-2xl p-4 border animate-fade-up max-w-xs"
              style={{borderColor:`${selectedNode.color}30`}}>
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 rounded-full" style={{background:selectedNode.color}} />
                <span className="mono text-xs font-bold uppercase" style={{color:selectedNode.color}}>{selectedNode.label}</span>
              </div>
              <p className="text-white/50 text-xs leading-relaxed">{selectedNode.detail}</p>
              <p className="mono text-xs text-white/20 mt-2">Group: {selectedNode.group}</p>
            </div>
          )}

          {/* Legend */}
          <div className="absolute top-4 right-4 glass rounded-xl p-3 space-y-1.5">
            <p className="mono text-xs text-white/20 uppercase tracking-wider mb-2">Legend</p>
            {[
              {color:"#f59e0b",label:"You"},
              {color:"#60a5fa",label:"Travel"},
              {color:"#818cf8",label:"Career"},
              {color:"#fb923c",label:"Business"},
              {color:"#4ade80",label:"Fitness"},
              {color:"#f472b6",label:"Prefs"},
            ].map(l=>(
              <div key={l.label} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full shrink-0" style={{background:l.color}} />
                <span className="text-xs text-white/30">{l.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Memory panel */}
        <aside className="w-72 border-l border-white/[0.05] flex flex-col">
          <div className="p-4 border-b border-white/[0.04]">
            <p className="mono text-xs text-white/25 uppercase tracking-wider mb-3">Memory Entries</p>
            <div className="flex gap-1.5 flex-wrap">
              {categories.map(c=>(
                <button key={c} onClick={()=>setActiveFilter(c)}
                  className={`mono text-xs px-2.5 py-1 rounded-lg transition ${activeFilter===c?"glass-amber text-amber-400":"text-white/30 hover:text-white/60"}`}>
                  {c}
                </button>
              ))}
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {filteredMemory.map((e,i)=>(
              <div key={i} className="glass rounded-xl p-3 hover:border-amber-400/15 transition">
                <div className="flex items-start gap-2.5">
                  <span className="text-base shrink-0">{e.icon}</span>
                  <div className="min-w-0">
                    <p className="mono text-xs text-white/25 uppercase">{e.cat} · {e.key}</p>
                    <p className="text-white/70 text-sm mt-0.5">{e.val}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="p-4 border-t border-white/[0.04]">
            <button className="w-full glass rounded-xl py-3 text-xs text-white/30 hover:text-white/60 transition mono">
              + Add Memory Entry
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
