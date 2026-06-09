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
import { AlertTriangle, BookOpenCheck, BrainCircuit, FileText, GitBranch, Loader2, Network, Radio, RefreshCw, Send, ShieldAlert, Users } from "lucide-react";

import type { KnowledgeLossResponse, KnowledgePriority } from "@/types/knowledge-loss";

const priorityColor: Record<KnowledgePriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function KnowledgeLossPanel() {
  const [analysis, setAnalysis] = useState<KnowledgeLossResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/knowledge-loss/analyze", { cache: "no-store" });
      if (!isKnowledgeLoss(payload)) throw new Error("Malformed knowledge loss payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Knowledge Loss Prevention could not refresh organizational-memory intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateKnowledgeRisk = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/knowledge-loss/analyze",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildKnowledgeLossScenario()),
          cache: "no-store",
        },
        60000,
      );
      if (!isKnowledgeLoss(payload)) throw new Error("Malformed knowledge loss payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Knowledge Loss Prevention could not process the expertise-risk scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/knowledge-loss/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Knowledge loss stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing knowledge loss stream");
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
            if (isKnowledgeLoss(payload) && Date.now() > manualScenarioUntil.current) {
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
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadDefault]);

  const expertiseData = useMemo(
    () =>
      analysis?.expertiseProfiles.slice(0, 6).map((profile) => ({
        name: shortName(profile.employeeName),
        expertise: Math.round(profile.expertiseScore),
        loss: Math.round(profile.knowledgeLossProbability),
        docs: Math.round(profile.documentationCoverage),
      })) ?? [],
    [analysis],
  );

  const forecastData = useMemo(() => {
    const owner = analysis?.summary.topRiskOwner;
    return (
      analysis?.forecasts
        .filter((point) => point.employeeName === owner)
        .map((point) => ({
          day: `D${point.day}`,
          loss: Math.round(point.knowledgeLossProbability),
          disruption: Math.round(point.operationalDisruptionRisk),
          transfer: Math.round(point.transferCompletionProbability),
        })) ?? []
    );
  }, [analysis]);

  const heatmapData = useMemo(() => analysis?.memoryHeatmap.slice(0, 12) ?? [], [analysis]);
  const graphEdges = useMemo(() => analysis?.graphEdges.slice(0, 10) ?? [], [analysis]);

  return (
    <section data-testid="knowledge-loss-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Knowledge Loss Prevention</p>
            <h2 className="text-xl font-semibold text-white">Enterprise organizational-memory, expertise dependency, and SOP automation intelligence</h2>
            <p className="mt-2 max-w-5xl text-sm text-slate-500">
              Knowledge-intelligence dashboard, Expertise heatmaps, Knowledge dependency graphs, Organizational-memory analytics, Documentation coverage panels, Knowledge-risk visualizations, AI onboarding widgets, and Executive knowledge insights
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-knowledge-loss" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh memory
          </button>
          <button data-testid="simulate-knowledge-loss" onClick={() => void simulateKnowledgeRisk()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate loss
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Extracting expertise from chats, meetings, code, Jira, support tickets, SOPs, graph relationships, attrition risk, documentation coverage, and handoff readiness...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Sources" value={String(analysis.summary.sourcesAnalyzed)} />
            <Stat label="Experts" value={String(analysis.summary.expertsIdentified)} />
            <Stat label="Graph Nodes" value={String(analysis.summary.graphNodes)} />
            <Stat label="Graph Edges" value={String(analysis.summary.graphEdges)} />
            <Stat label="High Risk" value={String(analysis.summary.highRiskDependencies)} tone={analysis.summary.highRiskDependencies > 0 ? "risk" : "normal"} />
            <Stat label="Docs" value={String(analysis.summary.generatedDocuments)} />
            <Stat label="Top Risk" value={analysis.summary.topRiskOwner} tone={analysis.summary.knowledgeLossRisk >= 55 ? "risk" : "normal"} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BarChartIcon} label="Knowledge-risk visualizations" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={expertiseData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="expertise" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="docs" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="loss" radius={[3, 3, 0, 0]}>
                      {expertiseData.map((item) => (
                        <Cell key={item.name} fill={item.loss >= 75 ? "#FF3B6B" : item.loss >= 55 ? "#F6B44B" : "#64748b"} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <PanelTitle icon={Users} label="Knowledge-intelligence dashboard" />
              <div className="grid gap-3">
                {analysis.expertiseProfiles.slice(0, 3).map((profile) => (
                  <div key={profile.employeeId} className="border border-cyan/20 bg-panel/70 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-white">{profile.employeeName}</span>
                      <span className="text-xs text-cyan">{Math.round(profile.expertiseScore)}% expertise</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{profile.role} / {profile.team}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-500">
                      <span>{Math.round(profile.knowledgeLossProbability)}% loss</span>
                      <span>{Math.round(profile.operationalDisruptionRisk)}% disruption</span>
                      <span>{Math.round(profile.documentationCoverage)}% docs</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{profile.ownedSystems.slice(0, 3).join(" / ")}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Radio} label={`Executive knowledge insights: ${analysis.summary.topRiskOwner}`} />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="loss" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="disruption" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="transfer" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Network} label="Knowledge dependency graphs" />
              <div className="grid gap-2">
                {graphEdges.map((edge) => (
                  <div key={`${edge.source}-${edge.target}-${edge.relation}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{edge.relation.replaceAll("_", " ")}</span>
                      <span className="text-xs text-cyan">{Math.round(edge.strength)}% strength</span>
                    </div>
                    <p className="mt-2 truncate text-xs text-slate-400">{edge.source} {"->"} {edge.target}</p>
                    <div className="mt-2 h-1.5 bg-black/30">
                      <div className="h-full" style={{ width: `${Math.round(edge.risk)}%`, backgroundColor: edge.risk >= 70 ? "#FF3B6B" : edge.risk >= 45 ? "#F6B44B" : "#7CF0A6" }} />
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={AlertTriangle} label="Expertise heatmaps" />
              <div className="grid gap-2 sm:grid-cols-2">
                {heatmapData.map((point) => (
                  <div key={`${point.department}-${point.system}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[point.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{point.system}</p>
                        <p className="mt-1 text-xs text-slate-500">{point.department}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[point.priority] }}>{Math.round(point.knowledgeLossRisk)}%</span>
                    </div>
                    <div className="mt-3 grid gap-2">
                      <Meter label="Concentration" value={point.expertiseConcentration} risk />
                      <Meter label="Documentation" value={point.documentationCoverage} />
                      <Meter label="Redundancy" value={point.redundancyScore} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={FileText} label="Documentation coverage panels" />
              <div className="grid gap-2">
                {analysis.generatedDocuments.map((document) => (
                  <div key={document.documentId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{document.title}</span>
                      <span className="text-xs uppercase text-cyan">{document.documentType} / {Math.round(document.confidence * 100)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{document.content}</p>
                    <p className="mt-2 text-xs text-slate-500">Owner: {document.owner}. Coverage: {Math.round(document.coverageScore)}%.</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BookOpenCheck} label="AI onboarding widgets" />
              <div className="grid gap-2">
                {analysis.onboardingRoadmaps.slice(0, 4).map((roadmap) => (
                  <div key={`${roadmap.role}-${roadmap.focusArea}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{roadmap.focusArea}</span>
                      <span className="text-xs text-mint">{roadmap.estimatedDaysSaved.toFixed(1)}d saved</span>
                    </div>
                    <ul className="mt-2 grid gap-1 text-xs leading-5 text-slate-400">
                      {roadmap.steps.slice(0, 3).map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={ShieldAlert} label="Organizational-memory analytics" />
              <div className="grid gap-2">
                {analysis.alerts.map((alert) => (
                  <div key={`${alert.title}-${alert.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{alert.title}</span>
                      <span className="text-xs uppercase" style={{ color: priorityColor[alert.severity] }}>{alert.severity} / {Math.round(alert.probability)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.impact}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={GitBranch} label="Knowledge transfer recommendations" />
              <div className="grid gap-2">
                {analysis.recommendations.map((item) => (
                  <div key={item.title} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-medium text-white">{item.title}</span>
                      <span className="text-xs uppercase" style={{ color: priorityColor[item.priority] }}>{item.category} / {Math.round(item.confidence * 100)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.action}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.expectedImpact}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="text-xs uppercase text-cyan">Executive knowledge insights</div>
              <div className="mt-3 grid gap-2">
                {analysis.executiveInsights.map((insight) => (
                  <p key={insight} className="border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-400">{insight}</p>
                ))}
              </div>
              <p className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs leading-5 text-slate-500">
                Models: {analysis.model}. Sources: {analysis.sourceSystems.join(", ")}.
              </p>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function PanelTitle({ icon: Icon, label }: { icon: typeof BrainCircuit; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value, tone = "normal" }: { label: string; value: string; tone?: "normal" | "risk" }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className={`mt-2 block truncate text-lg font-semibold ${tone === "risk" ? "text-signal" : "text-white"}`}>{value}</strong>
    </div>
  );
}

function Meter({ label, value, risk = false }: { label: string; value: number; risk?: boolean }) {
  const normalized = Math.max(0, Math.min(100, value));
  const color = risk ? (normalized >= 70 ? "#FF3B6B" : normalized >= 45 ? "#F6B44B" : "#7CF0A6") : "#2EE9D3";
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2 text-[11px] uppercase text-slate-500">
        <span>{label}</span>
        <span>{Math.round(normalized)}%</span>
      </div>
      <div className="h-1.5 bg-black/30">
        <div className="h-full" style={{ width: `${Math.round(normalized)}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function shortName(value: string) {
  return value.split(" ")[0] ?? value;
}

async function fetchJson(input: string, init: RequestInit, timeoutMs = 30000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error("Knowledge loss request failed");
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isKnowledgeLoss(value: unknown): value is KnowledgeLossResponse {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<KnowledgeLossResponse>;
  return Boolean(candidate.model && candidate.summary?.topRiskOwner && Array.isArray(candidate.expertiseProfiles) && Array.isArray(candidate.graphEdges));
}

function buildKnowledgeLossScenario() {
  return {
    cycle_name: "Strategic Knowledge Loss Simulation",
    horizon_days: 75,
    target_role: "Platform Engineer",
    realtime: true,
    sources: [
      {
        source_id: "critical-k8s",
        title: "Kubernetes Disaster Recovery Review",
        source_type: "meeting",
        employee_id: "emp-critical",
        employee_name: "Critical Engineer",
        department: "Platform",
        team: "Infrastructure Reliability",
        role: "Senior DevOps Engineer",
        content: "Critical Engineer owns Kubernetes cluster rollback, Helm release recovery, ingress failover, Redis stream replay, deployment pipeline recovery, and production incident triage.",
        systems: ["Kubernetes Platform", "Deployment Pipeline"],
        skills: ["kubernetes", "deployment", "incident response", "redis"],
        contribution_count: 28,
        incident_resolutions: 10,
        docs_authored: 0,
        commit_count: 95,
        meeting_mentions: 14,
        attrition_risk: 0.92,
        seniority: 0.96,
        documentation_quality: 0.18,
        last_updated_days: 86,
        business_criticality: 0.99,
        redundancy_count: 0,
        handoff_readiness: 0.12,
        onboarding_relevance: 0.9,
      },
      {
        source_id: "stable-docs",
        title: "Analytics Onboarding Wiki",
        source_type: "documentation",
        employee_id: "emp-stable",
        employee_name: "Stable Documenter",
        department: "Analytics",
        team: "Data Products",
        role: "Analytics Lead",
        content: "Stable Documenter maintains a complete analytics onboarding wiki, SQL dashboard guide, rollback checklist, and cross-trained support process.",
        systems: ["Analytics Dashboard"],
        skills: ["documentation", "postgresql", "frontend"],
        contribution_count: 10,
        incident_resolutions: 1,
        docs_authored: 8,
        commit_count: 22,
        meeting_mentions: 2,
        attrition_risk: 0.08,
        seniority: 0.7,
        documentation_quality: 0.94,
        last_updated_days: 3,
        business_criticality: 0.55,
        redundancy_count: 4,
        handoff_readiness: 0.88,
        onboarding_relevance: 0.82,
      },
    ],
  };
}

const BarChartIcon = GitBranch;
