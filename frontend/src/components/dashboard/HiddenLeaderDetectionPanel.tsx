"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Brain,
  GitBranch,
  GraduationCap,
  Lightbulb,
  Loader2,
  MessageSquare,
  Network,
  RefreshCw,
  Send,
  Sparkles,
  Target,
  Trophy,
  UserCheck,
  Users,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  HiddenLeaderAssistantResponse,
  HiddenLeaderDetectionResponse,
  HiddenLeaderRequest,
  TalentRiskLevel,
} from "@/types/hidden-leader";

const riskTone: Record<TalentRiskLevel, string> = {
  low: "border-mint/35 bg-mint/10 text-mint",
  medium: "border-cyan/35 bg-cyan/10 text-cyan",
  high: "border-amber/35 bg-amber/10 text-amber",
  critical: "border-rose/35 bg-rose/10 text-rose",
};

const defaultRequest: HiddenLeaderRequest = {
  cycleName: "Realtime Hidden Leader Detection Review",
  horizonMonths: 24,
  minCandidateScore: 60,
  includeOrganizationalGraph: true,
  includeTalentMarketplace: true,
  includeInnovationEngine: true,
};

const quickPrompts = [
  "Who are our future leaders?",
  "Which employee has the highest leadership potential?",
  "Who is influencing teams the most?",
  "Which employee should be promoted?",
  "Who is our most innovative contributor?",
  "Who are our knowledge leaders?",
];

export function HiddenLeaderDetectionPanel() {
  const [analysis, setAnalysis] = useState<HiddenLeaderDetectionResponse | null>(null);
  const [assistant, setAssistant] = useState<HiddenLeaderAssistantResponse | null>(null);
  const [question, setQuestion] = useState(quickPrompts[0]);
  const [request] = useState<HiddenLeaderRequest>(defaultRequest);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUntil.current = 0;
    try {
      const response = await fetch("/api/talent/hidden-leaders/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Hidden Leader default failed");
      setAnalysis((await response.json()) as HiddenLeaderDetectionResponse);
      setStreamStatus((current) => (current === "connecting" ? "polling" : current));
    } catch {
      setError("Hidden Leader Detection could not load live talent intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const analyze = useCallback(async () => {
    setRunning(true);
    setError("");
    manualUntil.current = Date.now() + 30000;
    try {
      const response = await fetch("/api/talent/hidden-leaders/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toSnake(request)),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Hidden Leader analysis failed");
      setAnalysis((await response.json()) as HiddenLeaderDetectionResponse);
    } catch {
      setError("Hidden Leader Detection could not run the talent intelligence scenario.");
    } finally {
      setRunning(false);
    }
  }, [request]);

  const ask = useCallback(async (override?: string) => {
    const prompt = override ?? question;
    if (!prompt.trim()) return;
    setRunning(true);
    setError("");
    try {
      const response = await fetch("/api/talent/hidden-leaders/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: prompt, session_id: "hidden-leader-dashboard", horizon_months: request.horizonMonths }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Hidden Leader assistant failed");
      setAssistant((await response.json()) as HiddenLeaderAssistantResponse);
    } catch {
      setError("Talent AI Assistant could not answer the leadership question.");
    } finally {
      setRunning(false);
    }
  }, [question, request.horizonMonths]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDefault();
      void ask(quickPrompts[0]);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [ask, loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/talent/hidden-leaders/stream");
    source.addEventListener("hidden_leader_detection", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as HiddenLeaderDetectionResponse;
        if (Date.now() > manualUntil.current) setAnalysis(payload);
        setStreamStatus("live");
        setLoading(false);
      } catch {
        setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((current) => (current === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const candidateBars = useMemo(
    () =>
      analysis?.hiddenLeaderCandidates.slice(0, 7).map((candidate) => ({
        name: firstName(candidate.employeeName),
        leadership: Math.round(candidate.hiddenLeaderScore),
        influence: Math.round(candidate.influenceScore),
        innovation: Math.round(candidate.innovationScore),
        knowledge: Math.round(candidate.knowledgeLeadershipScore),
      })) ?? [],
    [analysis],
  );

  const scorecardBars = useMemo(
    () =>
      analysis?.leadershipScorecards.slice(0, 7).map((item) => ({
        name: firstName(item.employeeName),
        decision: Math.round(item.decisionMaking),
        coordination: Math.round(item.teamCoordination),
        communication: Math.round(item.communicationQuality),
        reliability: Math.round(item.reliability),
      })) ?? [],
    [analysis],
  );

  const forecastLines = useMemo(
    () =>
      analysis?.leadershipForecast.slice(0, 18).map((item) => ({
        name: `${firstName(item.employeeName)} M${item.forecastMonth}`,
        readiness: Math.round(item.readinessScore),
        manager: Math.round(item.managerPotential),
        executive: Math.round(item.executivePotential),
      })) ?? [],
    [analysis],
  );

  return (
    <section data-testid="hidden-leader-detection-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs uppercase text-cyan">
            <UserCheck className="size-4" />
            Hidden Leader Detection
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Talent intelligence system for informal leaders, innovators, mentors, experts, and future executives</h2>
          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-400">
            Graph influence, innovation signals, mentoring evidence, knowledge leadership, performance trends, and promotion forecasts are merged into one executive talent pipeline.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <button onClick={() => void analyze()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {running ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Run analysis
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Analyzing leadership signals, graph influence, mentoring evidence, innovation impact, and promotion readiness...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-9">
            <Metric icon={Users} label="Analyzed" value={String(analysis.summary.employeesAnalyzed)} />
            <Metric icon={UserCheck} label="Hidden leaders" value={String(analysis.summary.hiddenLeadersFound)} />
            <Metric icon={Target} label="Managers" value={String(analysis.summary.futureManagerCandidates)} />
            <Metric icon={Trophy} label="Executives" value={String(analysis.summary.futureExecutiveCandidates)} />
            <Metric icon={Lightbulb} label="Innovators" value={String(analysis.summary.innovationLeaders)} />
            <Metric icon={GraduationCap} label="Knowledge" value={String(analysis.summary.knowledgeLeaders)} />
            <Metric icon={Brain} label="Readiness" value={`${Math.round(analysis.summary.productionReadinessScore)}%`} />
            <Metric icon={Sparkles} label="Wow" value={`${Math.round(analysis.summary.judgeWowFactorScore)}%`} />
            <Metric icon={MessageSquare} label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <Panel title="Leadership potential rankings" icon={Trophy}>
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.hiddenLeaderCandidates.slice(0, 6).map((candidate) => (
                  <div key={candidate.employeeId} className="min-w-0 border border-line/60 bg-void/35 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-white">{candidate.employeeName}</p>
                        <p className="mt-1 text-xs text-slate-500">{candidate.currentRole} - {candidate.recommendedFutureRole}</p>
                      </div>
                      <span className="shrink-0 text-sm font-semibold text-cyan">{Math.round(candidate.hiddenLeaderScore)}%</span>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2">
                      <MiniStat label="Influence" value={`${Math.round(candidate.influenceScore)}%`} />
                      <MiniStat label="Innovation" value={`${Math.round(candidate.innovationScore)}%`} />
                      <MiniStat label="Knowledge" value={`${Math.round(candidate.knowledgeLeadershipScore)}%`} />
                    </div>
                    <p className="mt-3 text-xs leading-5 text-slate-400">{candidate.whyHidden}</p>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Talent AI assistant" icon={MessageSquare}>
              <div className="flex flex-wrap gap-2">
                {quickPrompts.slice(0, 4).map((prompt) => (
                  <button key={prompt} onClick={() => { setQuestion(prompt); void ask(prompt); }} className="border border-line/70 bg-panel/65 px-2 py-1 text-xs text-slate-300">
                    {prompt}
                  </button>
                ))}
              </div>
              <div className="mt-3 flex gap-2">
                <input value={question} onChange={(event) => setQuestion(event.target.value)} className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan/60" />
                <button onClick={() => void ask()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {running ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              {assistant ? (
                <div className="mt-4 border border-line/60 bg-void/35 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs uppercase text-cyan">{assistant.intent.replaceAll("_", " ")}</span>
                    <span className="text-xs text-slate-500">{Math.round(assistant.confidence * 100)}% confidence</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-200">{assistant.answer}</p>
                  <ul className="mt-3 space-y-2">
                    {assistant.recommendedActions.slice(0, 3).map((action) => (
                      <li key={action} className="text-xs leading-5 text-slate-400">{action}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <ChartPanel title="Leadership score mix" icon={Brain}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={candidateBars}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263143" />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#101827", border: "1px solid #253047", color: "#e5edf7" }} />
                  <Bar dataKey="leadership" fill="#4dd5ff" />
                  <Bar dataKey="influence" fill="#7CF0A6" />
                  <Bar dataKey="innovation" fill="#F6B44B" />
                  <Bar dataKey="knowledge" fill="#C084FC" />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>

            <ChartPanel title="Scorecard evidence" icon={Target}>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={scorecardBars}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263143" />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#101827", border: "1px solid #253047", color: "#e5edf7" }} />
                  <Bar dataKey="decision" fill="#4dd5ff" />
                  <Bar dataKey="coordination" fill="#7CF0A6" />
                  <Bar dataKey="communication" fill="#F6B44B" />
                  <Bar dataKey="reliability" fill="#FF6B9C" />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>

            <ChartPanel title="Leadership readiness timeline" icon={GitBranch}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={forecastLines}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#263143" />
                  <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 10 }} interval={1} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#101827", border: "1px solid #253047", color: "#e5edf7" }} />
                  <Line type="monotone" dataKey="readiness" stroke="#4dd5ff" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="manager" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="executive" stroke="#F6B44B" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </ChartPanel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
            <Panel title="Influence leaders and graph evidence" icon={Network}>
              <div className="space-y-3">
                {analysis.influenceAnalysis.slice(0, 5).map((item) => (
                  <div key={item.employeeId} className="border border-line/60 bg-void/35 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-white">{item.employeeName}</div>
                        <div className="mt-1 text-xs text-slate-500">{item.consultedByTeams.slice(0, 3).join(", ")}</div>
                      </div>
                      <span className="text-sm font-semibold text-cyan">{Math.round(item.influenceScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.graphEvidence[0]}</p>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Innovation, knowledge, and promotion actions" icon={Sparkles}>
              <div className="grid gap-3 lg:grid-cols-3">
                <MiniList title="Innovation leaders" rows={analysis.innovationLeaders.slice(0, 4).map((item) => `${item.employeeName}: ${Math.round(item.innovationScore)}%`)} />
                <MiniList title="Knowledge leaders" rows={analysis.knowledgeLeaders.slice(0, 4).map((item) => `${item.employeeName}: ${Math.round(item.knowledgeLeadershipScore)}%`)} />
                <MiniList title="Problem solvers" rows={analysis.problemSolvingIntelligence.slice(0, 4).map((item) => `${item.employeeName}: ${Math.round(item.problemSolvingScore)}%`)} />
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {analysis.promotionRecommendations.slice(0, 4).map((item) => (
                  <div key={item.recommendationId} className="border border-line/60 bg-void/35 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-medium text-white">{item.employeeName}</div>
                      <span className={`border px-2 py-1 text-xs ${riskTone[item.priority]}`}>{item.priority}</span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-200">{item.action}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{item.expectedBusinessImpact}</p>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <Panel title="Graph integration" icon={GitBranch}>
              <div className="grid gap-2 sm:grid-cols-2">
                <MiniStat label="Influence relationships" value={String(analysis.graphIntegration.influenceRelationshipsAnalyzed)} />
                <MiniStat label="Knowledge relationships" value={String(analysis.graphIntegration.knowledgeRelationshipsAnalyzed)} />
                <MiniStat label="Communication graph" value={analysis.graphIntegration.communicationGraphStatus} />
                <MiniStat label="Knowledge graph" value={analysis.graphIntegration.knowledgeGraphStatus} />
              </div>
              <ul className="mt-3 space-y-2">
                {analysis.graphIntegration.graphEvidence.slice(0, 3).map((item) => (
                  <li key={item} className="text-xs leading-5 text-slate-400">{item}</li>
                ))}
              </ul>
            </Panel>

            <Panel title="Digital twin sync" icon={Brain}>
              <div className="space-y-2">
                {analysis.digitalTwinSync.map((item) => (
                  <div key={item.twin} className="border border-line/60 bg-void/35 p-2">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">{item.twin.replaceAll("_", " ")}</span>
                      <span className="text-xs text-cyan">{item.status}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{item.update}</p>
                  </div>
                ))}
              </div>
            </Panel>

            <Panel title="Talent intelligence council" icon={Users}>
              <div className="space-y-2">
                {analysis.agentCouncil.map((agent) => (
                  <div key={agent.agent} className="border border-line/60 bg-void/35 p-2">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-medium text-white">{agent.agent}</span>
                      <span className="text-xs text-cyan">{Math.round(agent.confidence * 100)}%</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{agent.recommendation}</p>
                  </div>
                ))}
              </div>
            </Panel>
          </div>

          <div className="mt-4 border border-cyan/30 bg-cyan/10 p-3 text-sm text-cyan">{analysis.finalVerdict}</div>
        </>
      ) : null}
    </section>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="min-w-0 overflow-hidden border border-line/80 bg-panel2/70 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
        <Icon className="size-4 text-cyan" />
        {title}
      </div>
      {children}
    </div>
  );
}

function ChartPanel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="min-w-0 overflow-hidden border border-line/80 bg-panel2/70 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white">
        <Icon className="size-4 text-cyan" />
        {title}
      </div>
      <div className="h-[260px] min-w-0">{children}</div>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="min-w-0 border border-line bg-void/45 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs uppercase text-slate-500">{label}</span>
        <Icon className="size-4 shrink-0 text-cyan" />
      </div>
      <div className="mt-2 truncate text-lg font-semibold text-white">{value}</div>
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border border-line/60 bg-panel/60 p-2">
      <div className="truncate text-[11px] uppercase text-slate-500">{label}</div>
      <div className="mt-1 truncate text-sm font-medium text-white">{value}</div>
    </div>
  );
}

function MiniList({ title, rows }: { title: string; rows: string[] }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="text-sm font-medium text-white">{title}</div>
      <ul className="mt-2 space-y-2">
        {rows.map((row) => (
          <li key={row} className="text-xs leading-5 text-slate-400">{row}</li>
        ))}
      </ul>
    </div>
  );
}

function firstName(name: string) {
  return name.split(" ")[0] || name;
}

function toSnake(value: unknown): unknown {
  if (Array.isArray(value)) return value.map((item) => toSnake(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, nested]) => [
        key.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`),
        toSnake(nested),
      ]),
    );
  }
  return value;
}
