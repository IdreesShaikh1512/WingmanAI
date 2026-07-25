"use client";
import { useState, useEffect, useCallback } from "react";
import type { Reminder } from "@/lib/api";

interface ReminderToast {
  reminder: Reminder;
  id: string;
}

function playChime() {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    const ctx = new AudioCtx();
    const notes = [523.25, 659.25, 783.99]; // C5, E5, G5
    notes.forEach((freq, i) => {
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = "sine";
      osc.frequency.value = freq;
      const t = ctx.currentTime + i * 0.15;
      gain.gain.setValueAtTime(0.25, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.5);
      osc.start(t);
      osc.stop(t + 0.5);
    });
  } catch { /* AudioContext may not be available */ }
}

async function requestPermission() {
  if (typeof Notification !== "undefined" && Notification.permission === "default") {
    await Notification.requestPermission();
  }
}

function showBrowserNotification(title: string, body: string) {
  if (typeof Notification !== "undefined" && Notification.permission === "granted") {
    new Notification(`🔔 ${title}`, { body });
  }
}

const SNOOZE_OPTIONS = [
  { label: "5 min",  ms: 5   * 60 * 1000 },
  { label: "15 min", ms: 15  * 60 * 1000 },
  { label: "1 hr",   ms: 60  * 60 * 1000 },
];

const DISMISSED_KEY = "wingman_dismissed_reminders";

function getDismissed(): Record<string, number> {
  try {
    return JSON.parse(localStorage.getItem(DISMISSED_KEY) ?? "{}");
  } catch {
    return {};
  }
}
function saveDismissed(map: Record<string, number>) {
  localStorage.setItem(DISMISSED_KEY, JSON.stringify(map));
}

interface ReminderSystemProps {
  reminders: Reminder[];
  onRefresh: () => void;
}

export function ReminderSystem({ reminders, onRefresh }: ReminderSystemProps) {
  const [toasts, setToasts] = useState<ReminderToast[]>([]);

  useEffect(() => {
    requestPermission();
  }, []);

  const check = useCallback(() => {
    const now      = Date.now();
    const dismissed = getDismissed();

    for (const r of reminders) {
      if (r.is_sent) continue;
      const due = new Date(r.remind_at).getTime();
      if (due > now + 30_000) continue; // not due yet (allow 30s early)
      if (dismissed[r.id] && dismissed[r.id] > now) continue; // snoozed

      setToasts((prev) => {
        if (prev.some((t) => t.reminder.id === r.id)) return prev;
        playChime();
        showBrowserNotification("Reminder", r.title);
        return [...prev, { reminder: r, id: crypto.randomUUID() }];
      });
    }
  }, [reminders]);

  useEffect(() => {
    check();
    const id = setInterval(check, 15_000);
    return () => clearInterval(id);
  }, [check]);

  const dismiss = (toast: ReminderToast) => {
    const d = getDismissed();
    d[toast.reminder.id] = Date.now() + 24 * 60 * 60 * 1000; // dismissed for 24h
    saveDismissed(d);
    setToasts((p) => p.filter((t) => t.id !== toast.id));
  };

  const snooze = (toast: ReminderToast, ms: number) => {
    const d = getDismissed();
    d[toast.reminder.id] = Date.now() + ms;
    saveDismissed(d);
    setToasts((p) => p.filter((t) => t.id !== toast.id));
  };

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-20 right-4 z-50 space-y-3 max-w-sm w-full">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className="animate-fade-up glass rounded-2xl border border-amber-400/25 p-4 shadow-2xl shadow-black/50"
          style={{ boxShadow: "0 0 40px rgba(245,158,11,0.08), 0 20px 60px rgba(0,0,0,0.6)" }}
        >
          {/* Header */}
          <div className="flex items-start gap-3 mb-4">
            <div className="w-8 h-8 rounded-xl bg-amber-400/10 border border-amber-400/20 flex items-center justify-center shrink-0 animate-pulse-amber">
              <span className="text-amber-400 text-sm">🔔</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="mono text-xs text-amber-400 font-bold uppercase tracking-wider">
                Reminder Fired
              </p>
              <p className="text-white/80 text-sm mt-0.5 leading-snug">{toast.reminder.title}</p>
              <p className="mono text-xs text-white/25 mt-1">
                Scheduled: {new Date(toast.reminder.remind_at).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => dismiss(toast)}
              className="text-white/20 hover:text-white/50 transition text-xl leading-none shrink-0"
              aria-label="Dismiss reminder"
            >
              ×
            </button>
          </div>

          {/* Snooze options */}
          <div className="flex gap-2 flex-wrap">
            {SNOOZE_OPTIONS.map((opt) => (
              <button
                key={opt.label}
                onClick={() => snooze(toast, opt.ms)}
                className="flex-1 glass text-xs text-white/50 hover:text-amber-400 hover:border-amber-400/25 py-2 rounded-lg transition mono"
              >
                ⏱ {opt.label}
              </button>
            ))}
            <button
              onClick={() => dismiss(toast)}
              className="flex-1 bg-amber-400/10 border border-amber-400/20 text-amber-400 text-xs py-2 rounded-lg hover:bg-amber-400/20 transition mono font-bold"
            >
              ✓ Done
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
