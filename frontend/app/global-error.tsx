"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, padding: 0, backgroundColor: "#0a0a0c", color: "#fff", fontFamily: "sans-serif" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "100vh", padding: "20px", textAlign: "center" }}>
          <h2 style={{ fontSize: "24px", marginBottom: "8px" }}>Critical System Error</h2>
          <p style={{ opacity: 0.6, maxWidth: "400px", marginBottom: "24px" }}>
            {error.message || "Wingman OS encountered an unexpected error."}
          </p>
          <button
            onClick={() => reset()}
            style={{ padding: "10px 20px", backgroundColor: "#f59e0b", border: "none", borderRadius: "8px", fontWeight: "bold", cursor: "pointer" }}
          >
            Reset System
          </button>
        </div>
      </body>
    </html>
  );
}
