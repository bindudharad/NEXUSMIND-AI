"use client";

import { RotateCcw } from "lucide-react";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="grid min-h-screen place-items-center bg-void px-4 text-slate-100">
      <section className="max-w-lg border border-signal/40 bg-panel/90 p-6 shadow-signal">
        <p className="text-xs uppercase text-signal">Command center interrupted</p>
        <h1 className="mt-3 text-2xl font-semibold text-white">The command center hit a recoverable runtime fault.</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          NEXUSMIND isolated the failure boundary. Retry the command center stream.
        </p>
        <button
          onClick={reset}
          className="mt-5 inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-4 py-2 text-sm text-cyan"
        >
          <RotateCcw className="size-4" />
          Retry
        </button>
      </section>
    </main>
  );
}
