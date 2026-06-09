"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity, Brain, Flame, HeartPulse, Loader2, MessageSquareWarning, Radio, RefreshCw, Send, Sparkles, Users } from "lucide-react";

import type {
  CompanyEmotionMapResponse,
  EmotionAssistantResponse,
  EmotionForecastPoint,
  EmotionHealthStatus,
  EmotionHeatmapZone,
  EmotionPriority,
  EmotionRecommendation,
} from "@/types/company-emotion-map";

const priorityColor: Record<EmotionPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F97316",
  critical: "#FF3B6B",
};

const healthColor: Record<EmotionHealthStatus, string> = {
  healthy: "#7CF0A6",
  attention_needed: "#F6B44B",
  overloaded: "#F97316",
  critical: "#FF3B6B",
};

const retryDelay = (attempt: number) => new Promise((resolve) => window.setTimeout(resolve, 1200 * (attempt + 1)));

export function CompanyEmotionMapPanel() {
  const [analysis, setAnalysis] = useState<CompanyEmotionMapResponse | null>(null);
  const [assistant, setAssistant] = useState<EmotionAssistantResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("Which department is most stressed?");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [selectedZoneId, setSelectedZoneId] = useState("company");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          const payload = await fetchJson("/api/emotion/map/default");
          if (!isEmotionMap(payload)) throw new Error("Malformed emotion map");
          setAnalysis(payload);
          setStreamStatus((status) => (status === "connecting" ? "polling" : status));
          return;
        } catch {
          if (attempt === 2) throw new Error("Emotion radar payload unavailable");
          await retryDelay(attempt);
        }
      }
    } catch {
      setError("Company Emotion Map could not refresh live organizational emotion intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulatePressure = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson("/api/emotion/map/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildEngineersResignEmotionPayload()),
      });
      if (!isEmotionMap(payload)) throw new Error("Malformed emotion map");
      setAnalysis(payload);
      setSelectedZoneId("department:Engineering");
    } catch {
      setError("Company Emotion Map could not process the pressure scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    setAssistantLoading(true);
    try {
      const payload = await fetchJson("/api/emotion/map/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (isEmotionAssistant(payload)) setAssistant(payload);
    } catch {
      setAssistant(null);
    } finally {
      setAssistantLoading(false);
    }
  }, [question]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/emotion/map/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Emotion stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing emotion stream");
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
            if (!dataLine) continue;
            const payload = JSON.parse(dataLine.slice(6));
            if (isEmotionMap(payload) && Date.now() > manualScenarioUntil.current) {
              setAnalysis(payload);
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
      void loadDefault();
      void askAssistant();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [askAssistant, loadDefault]);

  const departmentChart = useMemo(
    () =>
      analysis?.departmentScores.map((department) => ({
        name: department.department,
        morale: Math.round(department.moraleScore),
        stress: Math.round(department.stressIndex),
        burnout: Math.round(department.burnoutScore),
        conflict: Math.round(department.conflictRisk),
        priority: department.priority,
      })) ?? [],
    [analysis],
  );

  const teamChart = useMemo(
    () =>
      analysis?.teamScores.slice(0, 8).map((team) => ({
        name: team.team.split(" ")[0],
        stress: Math.round(team.stressScore),
        burnout: Math.round(team.burnoutRisk),
        conflict: Math.round(team.conflictRisk),
        engagement: Math.round(team.engagementScore),
        priority: team.priority,
      })) ?? [],
    [analysis],
  );

  const forecastChart = useMemo(() => {
    if (!analysis) return [];
    const periods = ["30_days", "90_days", "6_months", "1_year"] as const;
    return periods.map((period) => {
      const points = analysis.forecasts.filter((item) => item.period === period && item.scope === "department");
      return {
        period: period.replace("_", " "),
        burnout: averageMetric(points, "burnout"),
        morale: averageMetric(points, "morale"),
        stress: averageMetric(points, "stress"),
        conflict: averageMetric(points, "conflict"),
      };
    });
  }, [analysis]);

  const radarNodes = useMemo(() => analysis?.emotion3dNodes.slice(0, 16) ?? [], [analysis]);
  const heatmapZones = useMemo(() => analysis?.heatmapZones ?? [], [analysis]);
  const selectedZone = useMemo(
    () => heatmapZones.find((zone) => zoneKey(zone) === selectedZoneId) ?? heatmapZones[0] ?? null,
    [heatmapZones, selectedZoneId],
  );

  return (
    <section data-testid="company-emotion-map-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <HeartPulse className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Organizational Emotion Intelligence</p>
            <h2 className="text-xl font-semibold text-white">AI Emotion Radar</h2>
            <p className="mt-2 max-w-5xl text-sm text-slate-500">
              Live workforce emotion intelligence across stress hotspots, burnout, morale, toxic teams, silent employees, 3D emotion maps, digital twins, and multi-agent recommendations.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh map
          </button>
          <button onClick={() => void simulatePressure()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Emotion Radar Demo: 30 engineers resign
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Scoring organizational sentiment, burnout, conflict, motivation, engagement, and heatmap forecasts...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-10">
            <Stat label="Emotion health" value={`${Math.round(analysis.summary.organizationalHealthScore)}%`} />
            <Stat label="Workforce signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Teams" value={String(analysis.summary.teamsAnalyzed)} />
            <Stat label="Departments" value={String(analysis.summary.departmentsAnalyzed)} />
            <Stat label="Stress zones" value={String(analysis.summary.highStressHotspots)} tone="risk" />
            <Stat label="Burnout zones" value={String(analysis.summary.highBurnoutHotspots)} tone="risk" />
            <Stat label="Conflict zones" value={String(analysis.summary.highConflictZones)} tone="risk" />
            <Stat label="Toxic teams" value={String(analysis.summary.toxicTeams)} tone="risk" />
            <Stat label="Happy teams" value={String(analysis.summary.happyTeams)} />
            <Stat label="Readiness" value={`${Math.round(analysis.summary.productionReadinessScore)}%`} />
            <Stat label="Innovation" value={`${Math.round(analysis.summary.innovationScore)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <EmotionRadarHeatmap
            zones={heatmapZones}
            selectedZone={selectedZone}
            selectedZoneId={selectedZoneId}
            onSelect={setSelectedZoneId}
          />

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <article className="border border-cyan/25 bg-slate-950/80 p-4">
              <SectionTitle icon={Sparkles} label="3D organizational emotion map" />
              <div className="relative h-80 overflow-hidden border border-line/70 bg-[radial-gradient(circle_at_50%_45%,rgba(46,233,211,0.18),rgba(15,23,42,0.2)_35%,rgba(2,6,23,0.92)_72%)]">
                <div className="absolute inset-x-8 bottom-10 h-px bg-cyan/30" />
                <div className="absolute left-1/2 top-1/2 h-48 w-48 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan/10" />
                {radarNodes.map((node, index) => (
                  <div
                    key={`${node.nodeId}-${index}`}
                    className="absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center gap-1"
                    title={`${node.label}: stress ${Math.round(node.stress)}, burnout ${Math.round(node.burnout)}, morale ${Math.round(node.morale)}`}
                    style={{
                      left: `${Math.max(8, Math.min(92, 50 + node.x * 9))}%`,
                      top: `${Math.max(10, Math.min(88, 52 - node.z * 9 - node.y * 2))}%`,
                    }}
                  >
                    <span
                      className="block rounded-full border border-white/20"
                      style={{
                        width: `${10 + node.intensity / 5}px`,
                        height: `${10 + node.intensity / 5}px`,
                        backgroundColor: node.color,
                        boxShadow: `0 0 ${10 + node.intensity / 2}px ${node.color}`,
                      }}
                    />
                    {index < 7 || node.scope === "department" ? (
                      <span className="max-w-[6.5rem] truncate border border-white/10 bg-slate-950/85 px-1.5 py-0.5 text-center text-[9px] uppercase leading-3 text-slate-300 shadow-control">
                        {node.label}
                      </span>
                    ) : null}
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs leading-5 text-slate-500">
                Z-axis maps conflict pressure, vertical lift maps morale, node glow maps stress/burnout intensity.
              </p>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={MessageSquareWarning} label="Toxic, happy, and silent signals" />
              <div className="grid gap-3">
                {analysis.toxicTeamRisks.slice(0, 3).map((team) => (
                  <SignalCard key={`toxic-${team.team}`} label={`${team.team} / ${team.classification}`} score={team.score} body={team.reason} action={team.recommendedAction} />
                ))}
                {analysis.happyTeamSignals.slice(0, 2).map((team) => (
                  <SignalCard key={`happy-${team.team}`} label={`${team.team} / ${team.classification}`} score={team.score} body={team.reason} action={team.recommendedAction} positive />
                ))}
                {analysis.silentEmployeeRisks.slice(0, 2).map((employee) => (
                  <SignalCard key={`silent-${employee.employeeId}`} label={`${employee.name} / silent risk`} score={employee.isolationRisk} body={employee.reason} action={employee.recommendedAction} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Activity} label="Department emotion map" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={departmentChart} margin={{ left: -24, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="morale" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="stress" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="burnout" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" radius={[3, 3, 0, 0]}>
                      {departmentChart.map((item) => (
                        <Cell key={item.name} fill={priorityColor[item.priority]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Flame} label="Burnout and morale forecast" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastChart} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="period" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="burnout" stroke="#F05D5E" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="morale" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="stress" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="conflict" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Users} label="Team emotion intelligence" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={teamChart} margin={{ left: -24, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="engagement" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="stress" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="burnout" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={MessageSquareWarning} label="Conflict detection" />
              <div className="grid gap-3">
                {analysis.conflictRisks.slice(0, 5).map((conflict) => (
                  <div key={`${conflict.sourceEntity}-${conflict.targetEntity}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[toPriority(conflict.conflictProbability)] }}>
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">
                          {conflict.sourceEntity} {"->"} {conflict.targetEntity}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">{conflict.reason}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[toPriority(conflict.conflictProbability)] }}>{Math.round(conflict.conflictProbability)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{conflict.recommendedAction}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Brain} label="Employee emotion analysis" />
              <div className="grid gap-2 md:grid-cols-2">
                {analysis.employeeScores.slice(0, 6).map((employee) => (
                  <div key={employee.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{employee.name}</p>
                        <p className="mt-1 text-xs text-slate-500">{employee.department} / {employee.team}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[employee.priority] }}>{Math.round(employee.psychologicalRisk)}%</span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                      <MiniMetric label="Stress" value={employee.stressScore} />
                      <MiniMetric label="Burnout" value={employee.burnoutScore} />
                      <MiniMetric label="Morale" value={employee.moraleScore} inverse />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <SectionTitle icon={Sparkles} label="Executive recommendations" />
              <div className="grid gap-3">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <RecommendationCard key={`${recommendation.category}-${recommendation.title}`} recommendation={recommendation} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Radio} label="Digital twin and workflow signals" />
              <div className="grid gap-2 md:grid-cols-2">
                {analysis.digitalTwinUpdates.slice(0, 6).map((item) => (
                  <p key={item} className="border border-line/60 bg-panel/60 p-3 text-xs text-slate-300">{item}</p>
                ))}
                {analysis.workflowTriggers.slice(0, 6).map((item) => (
                  <p key={item} className="border border-cyan/20 bg-cyan/10 p-3 text-xs text-cyan">{item}</p>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Brain} label="Emotion intelligence council" />
              <div className="grid gap-2">
                {analysis.agentCouncil.map((agent) => (
                  <div key={agent.agent} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-sm font-semibold text-white">{agent.agent}</p>
                      <span className="text-xs text-cyan">{Math.round(agent.confidence * 100)}%</span>
                    </div>
                    <p className="mt-1 text-xs uppercase text-slate-500">{agent.domain}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{agent.finding}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Radio} label="Privacy-safe emotion data pipeline" />
              <div className="grid gap-2">
                {analysis.dataPipeline.slice(0, 6).map((source) => (
                  <div key={source.source} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold capitalize text-white">{formatPipelineSource(source.source)}</span>
                      <span className="text-xs text-cyan">{source.signalsProcessed} signals</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{source.privacyControl}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Brain} label="Emotion AI assistant" />
              <div className="flex flex-wrap gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-panel px-3 py-2 text-sm text-slate-200 outline-none"
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              {assistant ? (
                <div className="mt-3 border border-line/60 bg-panel/60 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs uppercase text-cyan">{assistant.intent}</span>
                    <span className="text-xs text-slate-500">{Math.round(assistant.confidence * 100)}% confidence</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{assistant.answer}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {assistant.citedEntities.slice(0, 4).map((entity) => (
                      <span key={entity} className="border border-line/60 bg-panel2 px-2 py-1 text-xs text-slate-400">{entity}</span>
                    ))}
                  </div>
                </div>
              ) : null}
            </article>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {analysis.executiveInsights.slice(0, 4).map((insight, index) => (
              <p key={`${insight}-${index}`} className="border border-line/60 bg-panel2/60 p-3 text-sm leading-6 text-slate-300">
                {insight}
              </p>
            ))}
            <p className="border border-cyan/30 bg-cyan/10 p-3 text-sm font-semibold text-cyan">{analysis.finalVerdict}</p>
          </div>
        </>
      ) : null}
    </section>
  );
}

function formatPipelineSource(source: string) {
  if (source === "attendance") return "availability intelligence";
  return source.replaceAll("_", " ");
}

function SectionTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value, tone = "normal" }: { label: string; value: string; tone?: "normal" | "risk" }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-1 block truncate text-lg font-semibold ${tone === "risk" ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function EmotionRadarHeatmap({
  zones,
  selectedZone,
  selectedZoneId,
  onSelect,
}: {
  zones: EmotionHeatmapZone[];
  selectedZone: EmotionHeatmapZone | null;
  selectedZoneId: string;
  onSelect: (id: string) => void;
}) {
  const companyZones = zones.filter((zone) => zone.scope === "company");
  const departmentZones = zones.filter((zone) => zone.scope === "department");
  const teamZones = zones.filter((zone) => zone.scope === "team").slice(0, 10);

  return (
    <article
      data-testid="real-time-emotion-heatmap"
      className="mt-5 overflow-hidden border border-cyan/25 bg-[radial-gradient(circle_at_top_left,rgba(46,233,211,0.16),rgba(11,16,23,0.82)_38%,rgba(2,6,23,0.94))] shadow-control"
    >
      <div className="flex flex-col gap-3 border-b border-cyan/15 p-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-cyan">Real-Time Workforce Health Heatmap</p>
          <h3 className="mt-2 text-lg font-semibold text-white">Green healthy, yellow warning, orange overloaded, red critical</h3>
          <p className="mt-1 text-sm text-slate-500">
            Live zones are calculated from employee, team, department, and company digital twins, then updated through the emotion stream or simulation input.
          </p>
        </div>
        <HealthLegend />
      </div>

      <div className="grid gap-4 p-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          <HeatmapZoneGroup title="Company View" zones={companyZones} selectedZoneId={selectedZoneId} onSelect={onSelect} compact />
          <HeatmapZoneGroup title="Department View" zones={departmentZones} selectedZoneId={selectedZoneId} onSelect={onSelect} />
          <HeatmapZoneGroup title="Team View" zones={teamZones} selectedZoneId={selectedZoneId} onSelect={onSelect} />
        </div>

        <div className="border border-line/70 bg-panel/70 p-4">
          {selectedZone ? (
            <>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">AI Explanation</p>
                  <h4 className="mt-2 text-xl font-semibold text-white">{selectedZone.label}</h4>
                  <p className="mt-1 text-sm" style={{ color: selectedZone.color }}>{healthStatusLabel(selectedZone.healthStatus)}</p>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-semibold text-white">{Math.round(selectedZone.healthIndex)}</p>
                  <p className="text-xs uppercase text-slate-500">Team Health Index</p>
                </div>
              </div>

              <p className="mt-4 text-sm leading-6 text-slate-300">{selectedZone.explanation}</p>

              <div className="mt-4 grid grid-cols-2 gap-3">
                <ZoneMetric label="Stress" value={selectedZone.stressScore} />
                <ZoneMetric label="Workload" value={selectedZone.workloadScore} />
                <ZoneMetric label="Burnout 90d" value={selectedZone.forecast90dBurnout} />
                <ZoneMetric label="Conflict" value={selectedZone.conflictRisk} />
                <ZoneMetric label="Morale" value={selectedZone.moraleScore} inverse />
                <ZoneMetric label="Productivity" value={selectedZone.productivityHealthScore} inverse />
              </div>

              <div className="mt-4 grid gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-cyan">Recovery Recommendations</p>
                  <div className="mt-2 space-y-2">
                    {selectedZone.recommendations.slice(0, 4).map((action, index) => (
                      <p key={`${selectedZone.entityId}-recommendation-${index}`} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-300">
                        {action}
                      </p>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-cyan">Digital Twin Evidence</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {selectedZone.twinEvidence.slice(0, 4).map((item, index) => (
                      <span key={`${selectedZone.entityId}-twin-${index}`} className="border border-cyan/20 bg-cyan/10 px-2 py-1 text-[11px] text-cyan">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">Heatmap zone details will appear after the first emotion-map payload loads.</p>
          )}
        </div>
      </div>
    </article>
  );
}

function HeatmapZoneGroup({
  title,
  zones,
  selectedZoneId,
  onSelect,
  compact = false,
}: {
  title: string;
  zones: EmotionHeatmapZone[];
  selectedZoneId: string;
  onSelect: (id: string) => void;
  compact?: boolean;
}) {
  return (
    <section>
      <div className="mb-2 flex items-center justify-between gap-3">
        <h4 className="text-xs uppercase tracking-[0.18em] text-slate-400">{title}</h4>
        <span className="text-xs text-slate-500">{zones.length} zones</span>
      </div>
      <div className={`grid gap-2 ${compact ? "grid-cols-1" : "sm:grid-cols-2 xl:grid-cols-3"}`}>
        {zones.map((zone) => (
          <HeatmapZoneTile
            key={zoneKey(zone)}
            zone={zone}
            selected={zoneKey(zone) === selectedZoneId}
            onClick={() => onSelect(zoneKey(zone))}
          />
        ))}
      </div>
    </section>
  );
}

function HeatmapZoneTile({ zone, selected, onClick }: { zone: EmotionHeatmapZone; selected: boolean; onClick: () => void }) {
  const pulse = zone.healthStatus === "critical" || zone.healthStatus === "overloaded";
  return (
    <button
      type="button"
      onClick={onClick}
      className={`group min-h-32 border p-3 text-left transition duration-300 hover:-translate-y-0.5 hover:border-cyan/50 ${
        selected ? "border-cyan/60 ring-1 ring-cyan/50" : "border-line/70"
      }`}
      style={{
        background: `linear-gradient(135deg, ${zone.color}30, rgba(15, 23, 42, 0.82) 62%)`,
        boxShadow: pulse ? `0 0 26px ${zone.color}40` : undefined,
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{zone.label}</p>
          <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-slate-400">{zone.scope} / {zone.department}</p>
        </div>
        <span className={`block size-3 rounded-full ${pulse ? "animate-pulse" : ""}`} style={{ backgroundColor: zone.color, boxShadow: `0 0 14px ${zone.color}` }} />
      </div>
      <div className="mt-4 flex items-end justify-between gap-3">
        <div>
          <p className="text-2xl font-semibold text-white">{Math.round(zone.healthIndex)}</p>
          <p className="text-[11px] uppercase text-slate-500">Health Index</p>
        </div>
        <p className="text-right text-xs font-semibold uppercase" style={{ color: zone.color }}>{healthStatusLabel(zone.healthStatus)}</p>
      </div>
      <div className="mt-3 h-1.5 bg-black/35">
        <div className="h-full transition-all duration-700" style={{ width: `${Math.max(3, zone.healthIndex)}%`, backgroundColor: zone.color }} />
      </div>
    </button>
  );
}

function ZoneMetric({ label, value, inverse = false }: { label: string; value: number; inverse?: boolean }) {
  const risk = inverse ? 100 - value : value;
  const color = priorityColor[toPriority(risk)];
  return (
    <div className="border border-line/60 bg-panel2/60 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs uppercase text-slate-500">{label}</span>
        <span className="text-sm font-semibold" style={{ color }}>{Math.round(value)}</span>
      </div>
      <div className="mt-2 h-1.5 bg-black/35">
        <div className="h-full transition-all duration-700" style={{ width: `${Math.max(3, Math.min(100, value))}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function HealthLegend() {
  const items: Array<{ status: EmotionHealthStatus; label: string; range: string }> = [
    { status: "healthy", label: "Healthy", range: "80-100" },
    { status: "attention_needed", label: "Warning", range: "60-79" },
    { status: "overloaded", label: "Overloaded", range: "40-59" },
    { status: "critical", label: "Critical", range: "0-39" },
  ];
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span key={item.status} className="inline-flex items-center gap-2 border border-line/60 bg-panel2/70 px-2 py-1 text-[11px] uppercase text-slate-300">
          <span className="size-2.5 rounded-full" style={{ backgroundColor: healthColor[item.status] }} />
          {item.label} {item.range}
        </span>
      ))}
    </div>
  );
}

function MiniMetric({ label, value, inverse = false }: { label: string; value: number; inverse?: boolean }) {
  const risk = inverse ? 100 - value : value;
  const priority = toPriority(risk);
  return (
    <div>
      <div className="flex items-center justify-between gap-2 text-slate-500">
        <span>{label}</span>
        <span style={{ color: priorityColor[priority] }}>{Math.round(value)}</span>
      </div>
      <div className="mt-1 h-1 bg-black/30">
        <div className="h-full" style={{ width: `${Math.max(4, Math.min(100, value))}%`, backgroundColor: priorityColor[priority] }} />
      </div>
    </div>
  );
}

function RecommendationCard({ recommendation }: { recommendation: EmotionRecommendation }) {
  return (
    <div className="border border-cyan/20 bg-panel/70 p-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <p className="text-sm font-semibold text-white">{recommendation.title}</p>
        <span className="text-sm font-semibold" style={{ color: priorityColor[recommendation.priority] }}>{Math.round(recommendation.expectedImprovement)}%</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.action}</p>
      <p className="mt-2 text-[11px] uppercase text-slate-500">
        {recommendation.category} / {Math.round(recommendation.confidence * 100)}% / {recommendation.triggeredWorkflow}
      </p>
    </div>
  );
}

function SignalCard({ label, score, body, action, positive = false }: { label: string; score: number; body: string; action: string; positive?: boolean }) {
  const priority = positive ? "low" : toPriority(score);
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <p className="text-sm font-semibold text-white">{label}</p>
        <span className="text-sm font-semibold" style={{ color: priorityColor[priority] }}>{Math.round(score)}%</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{body}</p>
      <p className="mt-2 text-[11px] uppercase text-slate-500">{action}</p>
    </div>
  );
}

function averageMetric(points: EmotionForecastPoint[], metric: EmotionForecastPoint["metric"]) {
  const values = points.filter((point) => point.metric === metric).map((point) => point.projectedScore);
  if (!values.length) return 0;
  return Math.round(values.reduce((total, value) => total + value, 0) / values.length);
}

function toPriority(score: number): EmotionPriority {
  if (score >= 82) return "critical";
  if (score >= 64) return "high";
  if (score >= 38) return "medium";
  return "low";
}

function zoneKey(zone: EmotionHeatmapZone): string {
  return `${zone.scope}:${zone.entityId}`;
}

function healthStatusLabel(status: EmotionHealthStatus): string {
  return status.replace("_", " ");
}

async function fetchJson(input: string, init?: RequestInit): Promise<unknown> {
  const response = await fetch(input, { cache: "no-store", ...init });
  const text = await response.text();
  const payload = text ? (JSON.parse(text) as unknown) : {};
  if (!response.ok) throw new Error("Company emotion map request failed");
  return payload;
}

function isEmotionMap(value: unknown): value is CompanyEmotionMapResponse {
  const candidate = value as Partial<CompanyEmotionMapResponse> | null;
  return Boolean(
    candidate &&
      typeof candidate.model === "string" &&
      Array.isArray(candidate.employeeScores) &&
      Array.isArray(candidate.teamScores) &&
      Array.isArray(candidate.departmentScores) &&
      Array.isArray(candidate.heatmap) &&
      Array.isArray(candidate.heatmapZones) &&
      Array.isArray(candidate.conflictRisks) &&
      Array.isArray(candidate.forecasts) &&
      Array.isArray(candidate.emotion3dNodes) &&
      Array.isArray(candidate.agentCouncil) &&
      candidate.summary,
  );
}

function isEmotionAssistant(value: unknown): value is EmotionAssistantResponse {
  const candidate = value as Partial<EmotionAssistantResponse> | null;
  return Boolean(candidate && typeof candidate.answer === "string" && typeof candidate.intent === "string");
}

function buildEngineersResignEmotionPayload() {
  return {
    cycle_name: "Emotion Radar Demo - What if 30 engineers resign tomorrow?",
    horizon_days: 120,
    realtime: true,
    employees: [
      {
        employee_id: "emotion-crisis-001",
        name: "Engineering Resignation Incident Owner",
        team: "Backend Platform",
        department: "Engineering",
        project: "Payments Reliability",
        location: "Bangalore",
        role: "Incident Lead",
        survey_score: 38,
        communication_samples: [
          { channel: "chat", text: "Thirty engineers may resign tomorrow and the remaining team is exhausted, overloaded, and worried about delivery failure." },
          { channel: "email", text: "Engineering capacity is collapsing, Project Delta ownership is unclear, and overtime is becoming unsustainable." },
        ],
        workload_hours: 63,
        overtime_hours: 26,
        meeting_hours: 19,
        task_load: 128,
        focus_hours: 1.1,
        productivity_trend: -34,
        performance_trend: -18,
        recognition_count: 0,
        learning_participation: 18,
        collaboration_score: 42,
        manager_support_score: 36,
        conflict_events: 7,
        negative_interactions: 18,
        positive_interactions: 2,
        attrition_risk: 82,
      },
      {
        employee_id: "emotion-crisis-003",
        name: "Platform Backfill Lead",
        team: "Backend Platform",
        department: "Engineering",
        project: "Project Delta",
        location: "Bangalore",
        role: "Senior Engineer",
        survey_score: 36,
        communication_samples: [
          { channel: "meeting", text: "If the resignations happen, remaining engineers will inherit too many incidents and delivery commitments." },
        ],
        workload_hours: 67,
        overtime_hours: 24,
        meeting_hours: 18,
        task_load: 132,
        focus_hours: 0.9,
        productivity_trend: -38,
        performance_trend: -24,
        recognition_count: 0,
        learning_participation: 14,
        collaboration_score: 40,
        manager_support_score: 34,
        conflict_events: 6,
        negative_interactions: 17,
        positive_interactions: 1,
        attrition_risk: 86,
      },
      {
        employee_id: "emotion-crisis-002",
        name: "QA Escalation Lead",
        team: "Release Quality",
        department: "Quality",
        project: "Release Readiness",
        location: "Pune",
        role: "QA Lead",
        survey_score: 45,
        communication_samples: [
          { channel: "meeting", text: "QA is absorbing late requirements and the release conversation is tense." },
        ],
        workload_hours: 56,
        overtime_hours: 17,
        meeting_hours: 16,
        task_load: 118,
        focus_hours: 1.9,
        productivity_trend: -21,
        performance_trend: -11,
        recognition_count: 1,
        learning_participation: 24,
        collaboration_score: 47,
        manager_support_score: 44,
        conflict_events: 5,
        negative_interactions: 13,
        positive_interactions: 3,
        attrition_risk: 68,
      },
      {
        employee_id: "emotion-stable-001",
        name: "Finance Stabilizer",
        team: "Finance Ops",
        department: "Finance",
        project: "Billing Governance",
        location: "Mumbai",
        role: "Finance Analyst",
        survey_score: 86,
        communication_samples: [
          { channel: "chat", text: "The governance process is calm, clear, and the team has enough focus time." },
        ],
        workload_hours: 38,
        overtime_hours: 1,
        meeting_hours: 4,
        task_load: 58,
        focus_hours: 7.4,
        productivity_trend: 7,
        performance_trend: 5,
        recognition_count: 4,
        learning_participation: 68,
        collaboration_score: 88,
        manager_support_score: 86,
        conflict_events: 0,
        negative_interactions: 1,
        positive_interactions: 10,
        attrition_risk: 14,
      },
    ],
    interactions: [
      {
        source_team: "Backend Platform",
        target_team: "Release Quality",
        department: "Engineering",
        sentiment_alignment: -0.72,
        unresolved_issues: 9,
        escalation_count: 6,
        communication_volume: 46,
        evidence: ["Late requirement conflict", "Repeated release-blocker escalation", "Decision owner missing"],
      },
    ],
  };
}
