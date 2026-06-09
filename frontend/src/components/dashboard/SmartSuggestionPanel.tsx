"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Brain, CalendarMinus, Check, HeartPulse, Radio, RefreshCw, Shuffle, TrendingUp, UsersRound } from "lucide-react";

import type { SmartSuggestion, SmartSuggestionCategory, SmartSuggestionResponse } from "@/types/suggestions";

type SnakeRecord = Record<string, unknown>;

const categoryLabel: Record<SmartSuggestionCategory, string> = {
  meeting_reduction: "Meeting reduction",
  workload_redistribution: "Workload redistribution",
  wellness_break: "Wellness",
  team_optimization: "Team optimization",
  productivity_improvement: "Productivity",
};

const categoryColor: Record<SmartSuggestionCategory, string> = {
  meeting_reduction: "#2EE9D3",
  workload_redistribution: "#F6B44B",
  wellness_break: "#7CF0A6",
  team_optimization: "#8FA7FF",
  productivity_improvement: "#F05D5E",
};

export function SmartSuggestionPanel() {
  const [result, setResult] = useState<SmartSuggestionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [feedbackId, setFeedbackId] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const activeMode = useRef<"default" | "crisis">("default");

  async function loadSuggestions(mode: "default" | "crisis" = activeMode.current) {
    activeMode.current = mode;
    setLoading(true);
    setError("");
    try {
      const response =
        mode === "default"
          ? await fetch("/api/suggestions/feed", { cache: "no-store" })
          : await fetch("/api/suggestions/feed", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ scenario: "crisis", sensitivity: 0.78, feedback_weight: 0.4 }),
              cache: "no-store",
            });
      if (!response.ok) throw new Error("Smart suggestion request failed");
      setResult((await response.json()) as SmartSuggestionResponse);
    } catch {
      setError("Smart Suggestion Engine could not refresh recommendations.");
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(suggestion: SmartSuggestion) {
    setFeedbackId(suggestion.suggestionId);
    try {
      const response = await fetch("/api/suggestions/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suggestionId: suggestion.suggestionId, accepted: true, usefulnessScore: 5 }),
      });
      if (!response.ok) throw new Error("Smart suggestion feedback failed");
      setResult((current) =>
        current
          ? {
              ...current,
              suggestions: current.suggestions.map((item) =>
                item.suggestionId === suggestion.suggestionId ? { ...item, feedbackState: "accepted" } : item,
              ),
            }
          : current,
      );
    } catch {
      setError("Suggestion feedback could not be stored.");
    }
  }

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/suggestions/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing suggestion stream");
        const decoder = new TextDecoder();
        let buffer = "";
        setStreamStatus("streaming");
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";
          for (const event of events) {
            const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
            if (dataLine) {
              setResult(toCamel<SmartSuggestionResponse>(JSON.parse(dataLine.slice(6))));
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadSuggestions();
    }, 8200);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 15000);
    const interval = window.setInterval(() => {
      void loadSuggestions(activeMode.current);
    }, 14000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
      window.clearInterval(interval);
    };
  }, []);

  const chartData = useMemo(() => {
    if (!result) return [];
    return result.suggestions.map((suggestion) => ({
      name: categoryLabel[suggestion.category],
      impact: suggestion.impactScore,
      category: suggestion.category,
    }));
  }, [result]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Brain className="size-5 text-mint" />
          <div>
            <p className="text-xs uppercase text-mint">Smart Suggestion Engine</p>
            <h2 className="text-xl font-semibold text-white">Realtime enterprise productivity optimizer</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadSuggestions("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Refresh suggestions
          </button>
          <button
            onClick={() => void loadSuggestions("crisis")}
            className="inline-flex items-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-sm text-mint"
          >
            <Shuffle className="size-4" />
            Simulate optimization crisis
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-6 text-sm text-slate-400">Scoring meeting load, workload, wellness, team balance, and productivity interventions...</p> : null}

      {result ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Model" value={result.model} />
            <Stat label="Suggestions" value={String(result.summary.total)} />
            <Stat label="Critical" value={String(result.summary.critical)} />
            <Stat label="Avg Impact" value={`${Math.round(result.summary.averageImpact)}%`} />
            <Stat label="Confidence" value={`${Math.round(result.summary.averageConfidence * 100)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.78fr_1.22fr]">
            <div className="h-80 border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Radio className="size-4" />
                Suggestion impact ranking
              </div>
              <ResponsiveContainer width="100%" height="88%">
                <BarChart data={chartData} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="impact" radius={[3, 3, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell key={`${entry.name}-${entry.impact}`} fill={categoryColor[entry.category]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-3">
              {result.suggestions.map((suggestion) => (
                <article key={suggestion.suggestionId} className="border border-line/70 bg-panel2/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <CategoryIcon category={suggestion.category} />
                      <div>
                        <p className="text-xs uppercase text-slate-500">
                          {categoryLabel[suggestion.category]} / {suggestion.priority}
                        </p>
                        <h3 className="mt-1 text-base font-semibold text-white">{suggestion.title}</h3>
                      </div>
                    </div>
                    <span
                      className="border px-2 py-1 text-xs"
                      style={{ borderColor: `${categoryColor[suggestion.category]}66`, color: categoryColor[suggestion.category] }}
                    >
                      {Math.round(suggestion.impactScore)} impact
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{suggestion.action}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{suggestion.rationale}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {suggestion.evidence.slice(0, 4).map((item) => (
                      <span key={item} className="border border-line/60 bg-panel/60 px-2 py-1 text-xs text-slate-300">
                        {item}
                      </span>
                    ))}
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                    <span className="text-xs uppercase text-amber">
                      {suggestion.estimatedGain} / {suggestion.timeToImpactHours}h / {suggestion.sourceSystems.slice(0, 3).join(" + ")}
                    </span>
                    <button
                      onClick={() => void sendFeedback(suggestion)}
                      className="inline-flex items-center gap-2 border border-mint/35 bg-mint/10 px-3 py-2 text-xs text-mint"
                    >
                      <Check className="size-3.5" />
                      {feedbackId === suggestion.suggestionId || suggestion.feedbackState === "accepted" ? "Learning captured" : "Accept signal"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function CategoryIcon({ category }: { category: SmartSuggestionCategory }) {
  const className = "mt-1 size-4 text-mint";
  if (category === "meeting_reduction") return <CalendarMinus className={className} />;
  if (category === "workload_redistribution") return <Shuffle className={className} />;
  if (category === "wellness_break") return <HeartPulse className={className} />;
  if (category === "team_optimization") return <UsersRound className={className} />;
  return <TrendingUp className={className} />;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block break-words text-base text-white">{value}</strong>
    </div>
  );
}

function toCamel<T>(value: unknown): T {
  if (Array.isArray(value)) return value.map((item) => toCamel(item)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as SnakeRecord).map(([key, nested]) => [
        key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase()),
        toCamel(nested),
      ]),
    ) as T;
  }
  return value as T;
}
