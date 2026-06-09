"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { Brain, Flame, GitBranch, Lightbulb, Loader2, Radio, RefreshCw, Rocket, Send, Sparkles, Trophy, UserCheck, Users } from "lucide-react";

import type { InnovationAssistantResponse, InnovationPriority, InnovationResponse } from "@/types/innovation";

const priorityColor: Record<InnovationPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function InnovationScoringPanel() {
  const [analysis, setAnalysis] = useState<InnovationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [assistantQuestion, setAssistantQuestion] = useState("Who are our future leaders?");
  const [assistant, setAssistant] = useState<InnovationAssistantResponse | null>(null);
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/innovation/score", { cache: "no-store" });
      if (!isInnovationResponse(payload)) throw new Error("Malformed innovation payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Innovation Scoring System could not refresh live innovation intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateBreakthrough = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/innovation/score",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildInnovationPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isInnovationResponse(payload)) throw new Error("Malformed innovation payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Innovation Scoring System could not process the breakthrough idea scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    try {
      const payload = await fetchJson(
        "/api/innovation/assistant",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: assistantQuestion }),
          cache: "no-store",
        },
        45000,
      );
      if (isInnovationAssistantResponse(payload)) setAssistant(payload);
    } catch {
      setError("AI Innovation Detector assistant could not answer the talent discovery question.");
    }
  }, [assistantQuestion]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/innovation/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Innovation stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing innovation stream");
        const decoder = new TextDecoder();
        let buffer = "";
        streamStarted = true;
        window.clearTimeout(fallback);
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
            if (isInnovationResponse(payload) && Date.now() > manualScenarioUntil.current) {
              setAnalysis(payload);
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      } finally {
        window.clearTimeout(fallback);
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadDefault();
    }, 0);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 3200);
    const assistantRefresh = window.setTimeout(() => {
      void askAssistant();
    }, 1800);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
      window.clearTimeout(assistantRefresh);
    };
  }, [askAssistant, loadDefault]);

  const leaderboardData = useMemo(
    () =>
      analysis?.employeeScores.slice(0, 7).map((item) => ({
        name: item.employeeName.split(" ")[0],
        innovation: Math.round(item.innovationScore),
        originality: Math.round(item.originalityScore),
        impact: Math.round(item.ideaImpactScore),
      })) ?? [],
    [analysis],
  );

  const heatmapData = useMemo(
    () =>
      analysis?.teamHeatmap.slice(0, 8).map((item) => ({
        name: `${item.department.slice(0, 3)}-${item.team.split(" ")[0]}`,
        innovation: Math.round(item.innovationScore),
        creativity: Math.round(item.creativityDensity),
        adoption: Math.round(item.adoptionVelocity),
        influence: Math.round(item.crossFunctionalInfluence),
        priority: item.priority,
      })) ?? [],
    [analysis],
  );

  const ideaData = useMemo(
    () =>
      analysis?.ideaInsights.slice(0, 7).map((item) => ({
        name: item.employeeName.split(" ")[0],
        impact: Math.round(item.impactScore),
        originality: Math.round(item.originalityScore),
        feasibility: Math.round(item.feasibilityScore),
        adoption: Math.round(item.adoptionProbability),
      })) ?? [],
    [analysis],
  );

  const trendData = useMemo(
    () =>
      analysis?.trendPoints.map((item) => ({
        label: item.label,
        impact: Math.round(item.averageImpact),
        originality: Math.round(item.averageOriginality),
        adoption: Math.round(item.adoptionProbability),
      })) ?? [],
    [analysis],
  );

  const forecastTrend = useMemo(() => {
    const forecast = analysis?.impactForecasts[0];
    return forecast?.forecast.map((value, index) => ({ window: `T+${index + 1}`, impact: Math.round(value) })) ?? [];
  }, [analysis]);

  return (
    <section data-testid="innovation-scoring-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Lightbulb className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Innovation Scoring System</p>
            <h2 className="text-xl font-semibold text-white">
              Innovation analytics dashboard, creativity heatmaps, employee innovation leaderboards, idea-impact graphs, team innovation analytics, suggestion-quality charts, AI recommendation widgets, and executive innovation insights
            </h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-innovation-scoring" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh innovation
          </button>
          <button data-testid="simulate-innovation-scoring" onClick={() => void simulateBreakthrough()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate breakthrough
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Mining ideas, scoring originality, forecasting business impact, and ranking innovation contributors...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Ideas" value={String(analysis.summary.ideasAnalyzed)} />
            <Stat label="Contributor signals" value={String(analysis.summary.employeesRanked)} />
            <Stat label="High impact" value={String(analysis.summary.highImpactIdeas)} />
            <Stat label="Adopted" value={String(analysis.summary.adoptedOrPilotingIdeas)} />
            <Stat label="Innovation" value={`${Math.round(analysis.summary.averageInnovationScore)}%`} />
            <Stat label="Hidden talent" value={String(analysis.summary.hiddenTalentCount)} />
            <Stat label="Future leaders" value={String(analysis.summary.futureLeadersCount)} />
            <Stat label="Promotions" value={String(analysis.summary.promotionCandidates)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={UserCheck} label="Hidden talent discovery" />
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.hiddenTalent.slice(0, 4).map((talent) => (
                  <div key={talent.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{talent.employeeName}</p>
                        <p className="mt-1 text-xs text-slate-500">{talent.department} - {talent.team}</p>
                      </div>
                      <span className="text-sm font-semibold text-cyan">{Math.round(talent.hiddenTalentScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{talent.reason}</p>
                    <p className="mt-2 text-[11px] uppercase text-slate-500">
                      {talent.potential.replace("_", " ")} potential - {Math.round(talent.underRecognizedGap)} recognition gap
                    </p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Brain} label="Innovation AI assistant" />
              <div className="flex gap-2">
                <input
                  value={assistantQuestion}
                  onChange={(event) => setAssistantQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-panel px-3 py-2 text-sm text-slate-200 outline-none"
                  aria-label="Innovation assistant question"
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  <Send className="size-4" />
                  Ask
                </button>
              </div>
              {assistant ? (
                <div className="mt-3 border border-line/60 bg-panel/60 p-3">
                  <p className="text-sm leading-6 text-slate-300">{assistant.answer}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {assistant.citedEmployees.map((employee) => (
                      <span key={employee} className="border border-line bg-panel2 px-2 py-1 text-xs text-slate-400">{employee}</span>
                    ))}
                  </div>
                  {assistant.recommendedActions[0] ? <p className="mt-3 text-xs leading-5 text-cyan">{assistant.recommendedActions[0]}</p> : null}
                </div>
              ) : null}
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Trophy} label="Future leader prediction" />
              <div className="space-y-3">
                {analysis.leadershipPredictions.slice(0, 4).map((leader) => (
                  <div key={leader.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{leader.employeeName}</p>
                      <span className="text-sm font-semibold text-cyan">{Math.round(leader.leadershipPotential)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{leader.recommendedTrack}</p>
                    <p className="mt-2 text-[11px] uppercase text-slate-500">
                      Manager {Math.round(leader.futureManagerProbability)} - Architect {Math.round(leader.futureArchitectProbability)} - Exec {Math.round(leader.futureExecutiveProbability)}
                    </p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={GitBranch} label="Problem solving intelligence" />
              <div className="space-y-3">
                {analysis.problemSolvingInsights.slice(0, 4).map((solver) => (
                  <div key={solver.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{solver.employeeName}</p>
                      <span className="text-sm font-semibold text-mint">{Math.round(solver.problemSolvingScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{solver.strength}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Rocket} label="Growth and promotion recommendations" />
              <div className="space-y-3">
                {analysis.promotionRecommendations.slice(0, 4).map((promotion) => (
                  <div key={promotion.employeeId} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[promotion.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{promotion.employeeName}</p>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[promotion.priority] }}>{Math.round(promotion.readinessScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{promotion.targetProgram}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{promotion.action}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Trophy} label="Employee innovation leaderboards" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={leaderboardData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="innovation" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="originality" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="impact" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Sparkles} label="Innovation analytics dashboard" />
              <div className="space-y-3">
                {analysis.employeeScores.slice(0, 5).map((employee) => (
                  <div key={employee.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">#{employee.creativityRank} {employee.employeeName}</p>
                        <p className="mt-1 text-xs text-slate-500">{employee.department} - {employee.team}</p>
                      </div>
                      <span className="text-sm font-semibold text-cyan">{Math.round(employee.innovationScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{employee.topIdea}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Flame} label="Talent risk indicators" />
              <div className="space-y-3">
                {analysis.talentRisks.slice(0, 4).map((risk) => (
                  <div key={risk.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-white">{risk.employeeName}</p>
                      <span className="text-xs uppercase text-amber">{risk.criticalTalentRisk}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{risk.riskReason}</p>
                    <p className="mt-2 text-[11px] uppercase text-slate-500">Flight {Math.round(risk.flightRisk)} - Retention {Math.round(risk.retentionRisk)} - Burnout {Math.round(risk.burnoutRisk)}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Radio} label="Digital twin and marketplace integration" />
              <div className="grid gap-2 md:grid-cols-2">
                {[...analysis.digitalTwinUpdates.slice(0, 4), ...analysis.marketplaceUpdates.slice(0, 4)].map((update) => (
                  <p key={update} className="border border-line/60 bg-panel/60 p-3 text-xs text-slate-400">{update}</p>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Flame} label="Creativity heatmaps" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="creativity" radius={[3, 3, 0, 0]}>
                      {heatmapData.map((item) => (
                        <Cell key={item.name} fill={priorityColor[item.priority]} />
                      ))}
                    </Bar>
                    <Bar dataKey="innovation" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="adoption" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="influence" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Rocket} label="Idea-impact graphs" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastTrend} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="window" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="impact" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                {analysis.impactForecasts.slice(0, 3).map((forecast) => (
                  <p key={forecast.ideaId} className="border border-line/60 bg-panel/60 p-3 text-xs text-slate-400">
                    {forecast.title}: {Math.round(forecast.predictedBusinessImpact)} impact, {Math.round(forecast.productivityLiftPercent)}% productivity lift, ${Math.round(forecast.costSavingEstimate).toLocaleString()} modeled savings.
                  </p>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Users} label="Team innovation analytics" />
              <div className="space-y-3">
                {analysis.teamHeatmap.slice(0, 5).map((team) => (
                  <div key={`${team.department}-${team.team}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[team.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{team.department} / {team.team}</p>
                        <p className="mt-1 text-xs text-slate-500">{team.ideaCount} idea signal(s), {Math.round(team.crossFunctionalInfluence)} influence</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[team.priority] }}>
                        {Math.round(team.innovationScore)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={GitBranch} label="Suggestion-quality charts" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={ideaData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="impact" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="originality" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="feasibility" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="adoption" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.98fr_1.02fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Brain} label="AI recommendation widgets" />
              <div className="space-y-3">
                {analysis.recommendations.slice(0, 5).map((item) => (
                  <div key={`${item.category}-${item.title}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-semibold text-white">{item.title}</p>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[item.priority] }}>{Math.round(item.impactScore)}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{item.action}</p>
                    <p className="mt-2 text-[11px] uppercase text-slate-500">{item.category.replace("_", " ")} - {Math.round(item.confidence * 100)}% confidence</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Radio} label="Executive innovation insights" />
              <div className="grid gap-3">
                {analysis.executiveInsights.slice(0, 5).map((insight, index) => (
                  <p key={`${insight}-${index}`} className="border border-line/60 bg-panel/60 p-3 text-sm text-slate-300">
                    {insight}
                  </p>
                ))}
              </div>
              <div className="mt-4 h-48">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="label" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="impact" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="originality" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="adoption" stroke="#F6B44B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] uppercase text-slate-500">
                <Radio className="size-3 text-cyan" />
                {analysis.model}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

async function fetchJson(input: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    const text = await response.text();
    const payload = text ? (JSON.parse(text) as unknown) : {};
    if (!response.ok) throw new Error("Innovation request failed");
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function isInnovationResponse(payload: unknown): payload is InnovationResponse {
  const value = payload as Partial<InnovationResponse> | null;
  return Boolean(
    value &&
      typeof value.model === "string" &&
      Array.isArray(value.ideaInsights) &&
      Array.isArray(value.employeeScores) &&
      Array.isArray(value.hiddenTalent) &&
      Array.isArray(value.leadershipPredictions) &&
      Array.isArray(value.problemSolvingInsights) &&
      Array.isArray(value.growthForecasts) &&
      Array.isArray(value.talentRisks) &&
      Array.isArray(value.promotionRecommendations) &&
      Array.isArray(value.teamHeatmap) &&
      Array.isArray(value.impactForecasts) &&
      Array.isArray(value.trendPoints) &&
      Array.isArray(value.recommendations) &&
      value.summary,
  );
}

function isInnovationAssistantResponse(payload: unknown): payload is InnovationAssistantResponse {
  const value = payload as Partial<InnovationAssistantResponse> | null;
  return Boolean(
    value &&
      typeof value.model === "string" &&
      typeof value.answer === "string" &&
      Array.isArray(value.citedEmployees) &&
      Array.isArray(value.recommendedActions),
  );
}

function SectionTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-1 block text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function buildInnovationPayload() {
  return {
    cycle_name: "AI Innovation Breakthrough Scenario",
    horizon_days: 120,
    realtime: true,
    ideas: [
      {
        idea_id: "innovation-ui-breakthrough",
        employee_id: "innovation-ui-a",
        employee_name: "Employee A",
        department: "Engineering",
        team: "AI Platform",
        channel: "proposal",
        text: "Prototype an autonomous vector retrieval and deployment optimizer that predicts risky diffs, reduces latency, creates self-healing rollback plans, and saves release engineering hours.",
        adoption_stage: "piloting",
        reactions_count: 48,
        cross_team_votes: 21,
        collaboration_mentions: 15,
        implementation_progress: 0.68,
        estimated_hours_saved: 740,
        estimated_cost_saving: 260000,
        estimated_revenue_impact: 420000,
        feasibility_signal: 0.86,
        strategic_alignment: 0.94,
        novelty_claim: 0.92,
      },
      {
        idea_id: "innovation-ui-weak",
        employee_id: "innovation-ui-b",
        employee_name: "Employee B",
        department: "Operations",
        team: "Planning",
        channel: "chat",
        text: "Maybe we should have another meeting later and talk about improving the process when people have time.",
        adoption_stage: "submitted",
        reactions_count: 1,
        cross_team_votes: 0,
        collaboration_mentions: 0,
        implementation_progress: 0.02,
        estimated_hours_saved: 0,
        estimated_cost_saving: 0,
        estimated_revenue_impact: 0,
        feasibility_signal: 0.28,
        strategic_alignment: 0.2,
        novelty_claim: 0.12,
      },
    ],
  };
}
