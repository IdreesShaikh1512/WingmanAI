"use client";
import { useState, useRef, useCallback, useEffect } from "react";

interface VoiceModeProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

type VoiceState = "idle" | "listening" | "processing";

export function VoiceMode({ onTranscript, disabled }: VoiceModeProps) {
  const [state, setState] = useState<VoiceState>("idle");
  const [interim, setInterim] = useState("");
  const [bars, setBars] = useState<number[]>(Array(18).fill(3));
  const recognitionRef = useRef<any>(null);
  const animRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isSupported =
    typeof window !== "undefined" &&
    ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    if (animRef.current) { clearInterval(animRef.current); animRef.current = null; }
    setBars(Array(18).fill(3));
    setInterim("");
    setState("idle");
  }, []);

  const start = useCallback(() => {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR || disabled) return;
    const r = new SR();
    r.continuous = false;
    r.interimResults = true;
    r.lang = "en-US";
    r.onstart = () => {
      setState("listening");
      animRef.current = setInterval(
        () => setBars(Array(18).fill(0).map(() => 3 + Math.random() * 26)),
        70,
      );
    };
    r.onresult = (e: any) => {
      const t = Array.from(e.results)
        .map((r: any) => r[0].transcript)
        .join("");
      setInterim(t);
      if (e.results[e.results.length - 1].isFinal) {
        setState("processing");
        stop();
        setTimeout(() => { onTranscript(t); setState("idle"); }, 200);
      }
    };
    r.onerror = stop;
    r.onend   = () => setState((s) => (s === "listening" ? "idle" : s));
    r.start();
    recognitionRef.current = r;
  }, [disabled, onTranscript, stop]);

  useEffect(() => () => stop(), [stop]);

  if (!isSupported) return null;

  return (
    <div className="relative flex items-center">
      {state === "listening" && (
        <div className="absolute bottom-full right-0 mb-2 px-3 py-2 rounded-xl border border-red-500/25 bg-black/90 backdrop-blur-xl shadow-xl flex flex-col items-center gap-1.5">
          <div className="flex items-end gap-px h-8">
            {bars.map((h, i) => (
              <div
                key={i}
                className="w-1 rounded-full transition-all duration-75"
                style={{ height: `${h}px`, background: `rgba(239,68,68,${0.5 + (h / 30) * 0.5})` }}
              />
            ))}
          </div>
          {interim && (
            <p className="mono text-xs text-red-400/70 max-w-[180px] truncate">{interim}</p>
          )}
          <p className="mono text-xs text-white/20 animate-pulse">Listening...</p>
        </div>
      )}

      <button
        onClick={state === "listening" ? stop : start}
        disabled={disabled || state === "processing"}
        title="Voice input — speak your objective"
        aria-label={state === "listening" ? "Stop voice input" : "Start voice input"}
        className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all shrink-0 ${
          state === "listening"
            ? "bg-red-500/15 border border-red-500/40 shadow-[0_0_20px_rgba(239,68,68,0.25)]"
            : "glass hover:border-amber-400/30"
        }`}
      >
        {state === "listening" ? (
          <div className="w-3 h-3 rounded-sm bg-red-400" />
        ) : state === "processing" ? (
          <div className="w-3.5 h-3.5 border-2 border-amber-400/25 border-t-amber-400 rounded-full animate-spin" />
        ) : (
          <svg className="w-4 h-4 text-white/35" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z" />
            <path
              fillRule="evenodd"
              d="M19 11a1 1 0 0 0-2 0 5 5 0 0 1-10 0 1 1 0 0 0-2 0 7 7 0 0 0 6 6.92V20H9a1 1 0 0 0 0 2h6a1 1 0 0 0 0-2h-2v-2.08A7 7 0 0 0 19 11z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </button>
    </div>
  );
}
