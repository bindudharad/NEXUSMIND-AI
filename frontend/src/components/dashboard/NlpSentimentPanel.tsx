"use client";

import { MessageSquareText, Send, ShieldAlert } from "lucide-react";
import { useState } from "react";

import type { NLPAnalyzeResponse } from "@/types/nlp";

const sampleText = "I am exhausted and working late every night, but the team still expects weekend incident coverage.";

export function NlpSentimentPanel() {
  const [text, setText] = useState(sampleText);
  const [result, setResult] = useState<NLPAnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/nlp/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: "emp-live-001",
          department: "Engineering",
          channel: "chat",
          text,
        }),
      });
      if (!response.ok) throw new Error("Analysis failed");
      setResult((await response.json()) as NLPAnalyzeResponse);
    } catch {
      setError("NLP model could not analyze this message.");
    } finally {
      setLoading(false);
    }
  }

  const scores = result?.emotionScores;

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <MessageSquareText className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Realtime NLP Sentiment AI</p>
            <h2 className="text-xl font-semibold text-white">Employee communication analysis</h2>
          </div>
        </div>
        {result ? (
          <span className="border border-mint/40 bg-mint/10 px-3 py-1 text-sm text-mint">{result.model}</span>
        ) : null}
      </div>

      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        className="mt-5 min-h-28 w-full resize-none border border-line bg-void/70 p-4 text-sm leading-6 text-slate-100 outline-none transition focus:border-cyan/50"
      />

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button
          onClick={analyze}
          disabled={loading || text.trim().length < 2}
          className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-4 py-2 text-sm text-cyan disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Send className="size-4" />
          {loading ? "Analyzing" : "Analyze message"}
        </button>
        {error ? <span className="text-sm text-signal">{error}</span> : null}
      </div>

      {result && scores ? (
        <div className="mt-5 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
          <article className="border border-line/70 bg-panel2/65 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase text-slate-500">Sentiment</p>
                <strong className="mt-2 block text-3xl capitalize text-white">{result.sentiment}</strong>
                <p className="mt-2 text-sm text-slate-400">
                  Primary emotion: <span className="text-cyan">{result.primaryEmotion}</span> · confidence{" "}
                  {Math.round(result.confidence * 100)}%
                </p>
              </div>
              <span className="border border-cyan/30 bg-cyan/10 px-3 py-1 text-sm text-cyan">
                score {result.sentimentScore.toFixed(2)}
              </span>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">{result.recommendation}</p>
            {result.burnoutIndicators.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {result.burnoutIndicators.map((indicator) => (
                  <span key={indicator} className="border border-signal/40 bg-signal/10 px-2 py-1 text-xs text-signal">
                    {indicator}
                  </span>
                ))}
              </div>
            ) : null}
          </article>

          <article className="border border-line/70 bg-panel2/65 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm text-slate-400">
              <ShieldAlert className="size-4 text-amber" />
              Emotion risk vectors
            </div>
            {Object.entries(scores).map(([label, value]) => (
              <div key={label} className="mb-3 last:mb-0">
                <div className="flex justify-between text-xs uppercase text-slate-500">
                  <span>{label.replace(/([A-Z])/g, " $1")}</span>
                  <span>{Math.round(value * 100)}%</span>
                </div>
                <div className="mt-1 h-2 bg-line">
                  <div
                    className={`h-full ${value > 0.5 ? "bg-signal" : value > 0.28 ? "bg-amber" : "bg-mint"}`}
                    style={{ width: `${Math.round(value * 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </article>
        </div>
      ) : null}
    </section>
  );
}
