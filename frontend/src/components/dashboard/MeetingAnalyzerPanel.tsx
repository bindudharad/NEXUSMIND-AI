"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, CheckSquare, Loader2, MessageSquareText, Radio, RefreshCw, Send, UsersRound } from "lucide-react";

import type { MeetingAnalysisResponse, MeetingRiskSignal } from "@/types/meetings";

type SnakeRecord = Record<string, unknown>;

const sampleTranscript = `Priya: Project Alpha is delayed because the API latency work is still blocked by the data migration.
John: I am exhausted and working late every night. The same incident keeps coming back and the release owner is unclear.
Maya: We agreed to freeze non-essential scope and move QA capacity into the release lane.
John: John will optimize API latency before Friday and share the benchmark report.
Bianca: Assign migration validation to Bianca by tomorrow so Backend can focus on the release path.
Omar: The conversation is becoming tense. We need one decision owner and fewer status meetings.
Priya: Decision: Priya will run the dependency room daily and cancel low-signal recurring meetings this week.`;

const riskColor: Record<MeetingRiskSignal["severity"], string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function MeetingAnalyzerPanel() {
  const [transcript, setTranscript] = useState(sampleTranscript);
  const [analysis, setAnalysis] = useState<MeetingAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadSampleAnalysis = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/meetings/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("Meeting analysis failed");
      const payload = await response.json();
      if (!isMeetingAnalysisResponse(payload)) throw new Error("Invalid meeting analysis response");
      setAnalysis(payload);
    } catch {
      setError("AI Meeting Analyzer could not process this transcript.");
    } finally {
      setLoading(false);
    }
  }, []);

  const analyzeTranscript = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/meetings/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          meeting_id: "meeting-live-console",
          title: "Live Transcript Intelligence Review",
          duration_minutes: 44,
          department: "Engineering",
          transcript,
          realtime: true,
        }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Meeting analysis failed");
      const payload = await response.json();
      if (!isMeetingAnalysisResponse(payload)) throw new Error("Invalid meeting analysis response");
      setAnalysis(payload);
    } catch {
      setError("AI Meeting Analyzer could not process this transcript.");
    } finally {
      setLoading(false);
    }
  }, [transcript]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/meetings/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing meeting stream");
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
              const payload = toCamel<unknown>(JSON.parse(dataLine.slice(6)));
              if (isMeetingAnalysisResponse(payload)) {
                setAnalysis(payload);
                setLoading(false);
              } else {
                setStreamStatus("polling");
              }
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadSampleAnalysis();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadSampleAnalysis]);

  const speakerData = useMemo(
    () =>
      (analysis?.speakerAnalytics ?? []).map((speaker) => ({
        speaker: speaker.speaker,
        participation: speaker.participationPercent,
        stress: Math.round(speaker.stressScore * 100),
      })) ?? [],
    [analysis],
  );
  const topicData = useMemo(
    () =>
      (analysis?.topicClusters ?? []).slice(0, 6).map((topic) => ({
        topic: topic.label.split(" ").slice(0, 2).join(" "),
        repetition: Math.round(topic.semanticRepetitionScore),
        mentions: topic.mentions,
      })) ?? [],
    [analysis],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Meeting Waste Detector</p>
            <h2 className="text-xl font-semibold text-white">Transcript intelligence, repeated-topic detection, speaking balance, meeting ROI, and async/email verdicts</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadSampleAnalysis()}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Load sample
          </button>
          <button
            onClick={() => void analyzeTranscript()}
            className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Analyze transcript
          </button>
        </div>
      </div>

      <textarea
        value={transcript}
        onChange={(event) => setTranscript(event.target.value)}
        className="mt-5 min-h-36 w-full resize-none border border-line bg-void/70 p-4 text-sm leading-6 text-slate-100 outline-none transition focus:border-cyan/50"
      />

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Analyzing transcript turns, sentiment, blockers, ownership, and participation balance...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Model" value={analysis.model} />
            <Stat label="Productivity" value={`${Math.round(analysis.summary.productivityScore)}%`} />
            <Stat label="Waste" value={`${Math.round(analysis.summary.wastePercentage)}%`} />
            <Stat label="Repeated" value={`${Math.round(analysis.summary.repeatedTopicRate)}%`} />
            <Stat label="Cost waste" value={formatMoney(analysis.wasteEconomics.wastedCost)} />
            <Stat label="Stress" value={`${Math.round(analysis.summary.stressIndex * 100)}%`} />
            <Stat label="Actions" value={String(analysis.summary.actionItemCount)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-amber">
                <Radio className="size-4" />
                Meeting necessity and ROI
              </div>
              <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border border-line/60 bg-panel/60 p-3">
                <div>
                  <p className="text-xs uppercase text-slate-500">AI verdict</p>
                  <h3 className="mt-1 text-lg font-semibold text-white">{verdictLabel(analysis.necessityAssessment.verdict)}</h3>
                </div>
                <div className="text-right">
                  <p className="text-xs uppercase text-cyan">Confidence</p>
                  <strong className="text-2xl text-white">{Math.round(analysis.necessityAssessment.confidence * 100)}%</strong>
                </div>
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{analysis.necessityAssessment.rationale}</p>
              <p className="mt-3 border border-cyan/30 bg-cyan/10 px-3 py-2 text-sm leading-6 text-cyan">{analysis.necessityAssessment.asyncRecommendation}</p>
              <div className="mt-4 grid gap-2 md:grid-cols-3">
                <Stat label="Spent hours" value={`${analysis.wasteEconomics.employeeHoursSpent}h`} />
                <Stat label="Wasted hours" value={`${analysis.wasteEconomics.wastedHours}h`} />
                <Stat label="Weekly waste" value={`${analysis.wasteEconomics.weeklyWasteHoursEstimate}h`} />
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <MessageSquareText className="size-4" />
                Repeated-topic heatmap
              </div>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topicData} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="topic" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="repetition" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="mentions" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {analysis.topicClusters.slice(0, 3).map((topic) => (
                  <div key={topic.topicId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{topic.label}</h3>
                      <span className="text-xs text-amber">{topic.mentions} mentions / {Math.round(topic.semanticRepetitionScore)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{topic.representativePhrases[0]}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <MessageSquareText className="size-4" />
                AI meeting summary
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-300">{analysis.summaryText}</p>
              <div className="mt-4 grid gap-3 md:grid-cols-2">
                <ListBlock title="Key points" items={analysis.keyPoints} />
                <ListBlock title="Decisions" items={analysis.decisions} empty="No explicit decision detected" />
                <ListBlock title="Blockers" items={analysis.blockers} empty="No blockers detected" />
                <ListBlock title="Recommendations" items={analysis.recommendations} />
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <UsersRound className="size-4" />
                Speaker participation and stress
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={speakerData} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="speaker" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="participation" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="stress" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <CheckSquare className="size-4" />
                Extracted action items
              </div>
              <div className="grid gap-3">
                {analysis.actionItems.map((item) => (
                  <div key={`${item.owner}-${item.task}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{item.owner}</h3>
                      <span className="text-xs text-cyan">{Math.round(item.confidence * 100)}% confidence</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-300">{item.task}</p>
                    {item.deadline ? <p className="mt-1 text-xs text-amber">Due: {item.deadline}</p> : null}
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <Radio className="size-4" />
                Risk signals
              </div>
              <div className="grid gap-3">
                {analysis.riskSignals.map((risk) => (
                  <div key={risk.category} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium capitalize text-white">{risk.category.replace(/_/g, " ")}</h3>
                      <span style={{ color: riskColor[risk.severity] }} className="text-xs uppercase">
                        {risk.severity} / {Math.round(risk.score)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{risk.recommendation}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 border border-line/60 bg-panel/60 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-medium text-white">{analysis.overloadAnalytics.department} overload forecast</h3>
                  <span className="text-xs text-amber">{Math.round(analysis.overloadAnalytics.meetingLoadScore)} load / {Math.round(analysis.overloadAnalytics.productivityDragPercent)} drag</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{analysis.overloadAnalytics.forecast}</p>
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function ListBlock({ title, items, empty = "No items detected" }: { title: string; items: string[]; empty?: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <h3 className="text-xs uppercase text-slate-500">{title}</h3>
      <ul className="mt-2 grid gap-2 text-xs leading-5 text-slate-300">
        {(items.length ? items : [empty]).slice(0, 4).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block break-words text-base text-white">{value}</strong>
    </div>
  );
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function verdictLabel(value: MeetingAnalysisResponse["necessityAssessment"]["verdict"]) {
  return value
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
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

function isMeetingAnalysisResponse(value: unknown): value is MeetingAnalysisResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<MeetingAnalysisResponse>;
  return (
    typeof candidate.model === "string" &&
    Array.isArray(candidate.speakerAnalytics) &&
    Array.isArray(candidate.topicClusters) &&
    Array.isArray(candidate.actionItems) &&
    Array.isArray(candidate.riskSignals) &&
    typeof candidate.summary === "object" &&
    typeof candidate.necessityAssessment === "object" &&
    typeof candidate.wasteEconomics === "object" &&
    typeof candidate.overloadAnalytics === "object"
  );
}
