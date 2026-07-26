"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("App Error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white flex flex-col items-center justify-center p-6 text-center">
      <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mb-4 text-red-400 text-xl font-mono">
        !
      </div>
      <h2 className="text-xl font-bold mb-2">Something went wrong</h2>
      <p className="text-white/40 text-sm max-w-md mb-6">
        {error.message || "An unexpected error occurred in Wingman OS."}
      </p>
      <div className="flex gap-3">
        <button
          onClick={() => reset()}
          className="px-5 py-2.5 bg-amber-500 text-black font-medium text-sm rounded-lg hover:bg-amber-400 transition"
        >
          Try Again
        </button>
        <a
          href="/"
          className="px-5 py-2.5 bg-white/5 hover:bg-white/10 text-white/70 text-sm rounded-lg border border-white/10 transition"
        >
          Return Home
        </a>
      </div>
    </div>
  );
}
