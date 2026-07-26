import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white flex flex-col items-center justify-center p-6 text-center">
      <div className="text-6xl font-mono font-bold text-amber-500 mb-4">404</div>
      <h2 className="text-2xl font-bold mb-2">Page Not Found</h2>
      <p className="text-white/40 text-sm max-w-md mb-8">
        The requested route or mission workspace does not exist.
      </p>
      <Link
        href="/"
        className="px-6 py-3 bg-amber-500 text-black font-medium text-sm rounded-lg hover:bg-amber-400 transition"
      >
        Return to Wingman OS
      </Link>
    </div>
  );
}
