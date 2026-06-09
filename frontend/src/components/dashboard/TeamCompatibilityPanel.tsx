"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { GitBranch, Loader2, Network, Radio, RefreshCw, Send, ShieldAlert, UsersRound } from "lucide-react";

import type { TeamCompatibilityResponse, TeamConflictWarning } from "@/types/team-compatibility";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<TeamConflictWarning["severity"], string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function TeamCompatibilityPanel() {
  const [analysis, setAnalysis] = useState<TeamCompatibilityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadSample = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/team-compatibility/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("Team compatibility failed");
      setAnalysis((await response.json()) as TeamCompatibilityResponse);
    } catch {
      setError("Team Compatibility AI could not load the relationship graph.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runStressScenario = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/team-compatibility/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(stressScenarioPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Team compatibility failed");
      setAnalysis((await response.json()) as TeamCompatibilityResponse);
    } catch {
      setError("Team Compatibility AI could not process the stress scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/team-compatibility/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing team compatibility stream");
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
              setAnalysis(toCamel<TeamCompatibilityResponse>(JSON.parse(dataLine.slice(6))));
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
      void loadSample();
    }, 10600);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 16000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadSample]);

  const pairChart = useMemo(
    () =>
      analysis?.pairScores.slice(0, 8).map((pair) => ({
        pair: `${initials(pair.sourceName)}+${initials(pair.targetName)}`,
        compatibility: Math.round(pair.compatibilityScore),
        conflict: Math.round(pair.conflictProbability),
      })) ?? [],
    [analysis],
  );

  const heatmapPairs = analysis?.pairScores.slice(0, 10) ?? [];

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Network className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Team Compatibility AI</p>
            <h2 className="text-xl font-semibold text-white">Relationship graph, chemistry scoring, conflict prediction, and AI team formation</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadSample()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Load graph
          </button>
          <button onClick={() => void runStressScenario()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Stress test
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Scoring compatibility, workstyle clusters, burnout propagation, and team formation options...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Collaboration signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Pairs" value={String(analysis.summary.pairsAnalyzed)} />
            <Stat label="Compatibility" value={`${Math.round(analysis.summary.averageCompatibility)}%`} />
            <Stat label="Conflict" value={`${Math.round(analysis.summary.averageConflictProbability)}%`} />
            <Stat label="Team score" value={`${Math.round(analysis.summary.recommendedTeamScore)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <GitBranch className="size-4" />
                Compatibility graph
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                {heatmapPairs.map((pair) => (
                  <div key={`${pair.sourceId}-${pair.targetId}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-medium text-white">{initials(pair.sourceName)} + {initials(pair.targetName)}</span>
                      <span className="text-xs text-cyan">{Math.round(pair.compatibilityScore)}%</span>
                    </div>
                    <div className="mt-2 h-2 bg-void">
                      <div
                        className="h-2"
                        style={{
                          width: `${Math.round(pair.compatibilityScore)}%`,
                          background: pair.conflictProbability > 55 ? "#FF3B6B" : pair.compatibilityScore > 74 ? "#2EE9D3" : "#F6B44B",
                        }}
                      />
                    </div>
                    <p className="mt-2 text-xs uppercase text-slate-500">{pair.chemistryLabel}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={pairChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="pair" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="compatibility" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <UsersRound className="size-4" />
                Recommended project teams
              </div>
              <div className="grid gap-3">
                {analysis.teamRecommendations.slice(0, 3).map((team) => (
                  <div key={team.teamId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{team.title}</h3>
                      <span className="text-xs text-cyan">{Math.round(team.projectedVelocity)}% velocity</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{team.rationale}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {team.members.map((member) => (
                        <span key={member} className="border border-line/50 bg-void/70 px-2 py-1 text-xs text-slate-300">
                          {member}
                        </span>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-mint">Leader: {team.leader}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Conflict intelligence
              </div>
              <div className="grid gap-3">
                {(analysis.conflictWarnings.length ? analysis.conflictWarnings : emptyWarnings()).map((warning) => (
                  <div key={`${warning.employees.join("-")}-${warning.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{warning.employees.join(" + ")}</h3>
                      <span style={{ color: severityColor[warning.severity] }} className="text-xs uppercase">
                        {warning.severity} / {Math.round(warning.probability)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{warning.intervention}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Radio className="size-4" />
                Leadership and chemistry insights
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.leadershipMatches.slice(0, 4).map((match) => (
                  <div key={match.leaderId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{match.leaderName}</h3>
                      <span className="text-xs text-cyan">{Math.round(match.compatibilityScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{match.teamScope}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-2 text-sm leading-6 text-slate-300">
                {[...analysis.chemistryInsights, ...analysis.optimizationSuggestions].slice(0, 6).map((item) => (
                  <p key={item} className="border border-line/50 bg-panel/55 px-3 py-2">
                    {item}
                  </p>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function stressScenarioPayload() {
  return {
    project_name: "Critical Revenue Platform",
    required_skills: ["python", "api", "security", "mlops"],
    target_team_size: 3,
    employees: [
      {
        employee_id: "emp-compatible-a",
        name: "Employee A",
        role: "Backend Lead",
        department: "Engineering",
        skills: ["python", "api", "security"],
        work_style: "analytical",
        productivity_history: [0.9, 0.88, 0.91],
        stress_history: [0.24, 0.26, 0.28],
        sentiment_trend: 0.45,
        task_completion_rate: 0.91,
        meeting_participation: 0.48,
        collaboration_frequency: 0.9,
        leadership_score: 0.82,
        burnout_risk: 0.21,
        current_workload: 0.58,
        focus_ratio: 0.74,
      },
      {
        employee_id: "emp-compatible-b",
        name: "Employee B",
        role: "Reliability Engineer",
        department: "Platform",
        skills: ["python", "api", "mlops"],
        work_style: "supportive",
        productivity_history: [0.89, 0.91, 0.9],
        stress_history: [0.22, 0.25, 0.26],
        sentiment_trend: 0.5,
        task_completion_rate: 0.9,
        meeting_participation: 0.5,
        collaboration_frequency: 0.88,
        leadership_score: 0.66,
        burnout_risk: 0.2,
        current_workload: 0.56,
        focus_ratio: 0.7,
      },
      {
        employee_id: "emp-conflict-c",
        name: "Employee C",
        role: "Incident Commander",
        department: "Engineering",
        skills: ["incident", "backend", "security"],
        work_style: "decisive",
        productivity_history: [0.55, 0.51, 0.48],
        stress_history: [0.84, 0.89, 0.94],
        sentiment_trend: -0.7,
        task_completion_rate: 0.49,
        meeting_participation: 0.9,
        collaboration_frequency: 0.38,
        leadership_score: 0.58,
        burnout_risk: 0.88,
        current_workload: 0.96,
        focus_ratio: 0.2,
      },
    ],
    interactions: [
      {
        source_id: "emp-compatible-a",
        target_id: "emp-compatible-b",
        collaboration_frequency: 0.94,
        past_success_rate: 0.92,
        sentiment_alignment: 0.88,
        conflict_incidents: 0,
        meetings_together: 22,
      },
      {
        source_id: "emp-compatible-a",
        target_id: "emp-conflict-c",
        collaboration_frequency: 0.28,
        past_success_rate: 0.32,
        sentiment_alignment: 0.24,
        conflict_incidents: 6,
        meetings_together: 18,
      },
    ],
    realtime: true,
  };
}

function emptyWarnings(): TeamConflictWarning[] {
  return [
    {
      severity: "low",
      probability: 12,
      employees: ["No high-risk pair"],
      message: "No critical relationship warning detected.",
      intervention: "Maintain current team formation and revisit after sprint changes.",
    },
  ];
}

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
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
