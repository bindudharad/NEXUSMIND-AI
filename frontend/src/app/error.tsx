"use client";

import { RotateCcw } from "lucide-react";

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="cinematic-shell grid min-h-screen place-items-center px-4 text-slate-100">
      <section className="hud-panel max-w-lg p-6 shadow-signal">
        <div className="neural-mesh" />
        <div className="hud-content">
          <p className="premium-kicker text-signal">
            <RotateCcw className="size-3" />
            Command center interrupted
          </p>
          <h1 className="mt-4 text-2xl font-semibold text-white">The command center hit a recoverable runtime fault.</h1>
        <p className="mt-3 text-sm leading-6 text-slate-400">
          NEXUSMIND isolated the failure boundary. Retry the command center stream.
        </p>
        <button
          onClick={reset}
          className="cinematic-button mt-5 inline-flex h-10 items-center gap-2 px-4 text-sm text-cyan"
        >
          <RotateCcw className="size-4" />
          Retry
        </button>
        </div>
      </section>
    </main>
  );
}
