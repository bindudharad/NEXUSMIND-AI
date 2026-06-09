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
  AlertTriangle,
  Brain,
  GitBranch,
  Loader2,
  MessageSquare,
  Network,
  Radio,
  RefreshCw,
  Send,
  UsersRound,
  Waypoints,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  OrgGraphEdge,
  OrgGraphNode,
  OrgEdgeType,
  OrgNodeType,
  OrgRiskLevel,
  OrganizationalAssistantResponse,
  OrganizationalOptimizerResponse,
  OrganizationalRecommendation,
} from "@/types/organizational-optimizer";

const riskColor: Record<OrgRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

const nodeColor: Record<OrgNodeType, string> = {
  employee: "#38BDF8",
  manager: "#F6B44B",
  team: "#2EE9D3",
  department: "#A78BFA",
  project: "#7CF0A6",
  location: "#94A3B8",
  skill: "#FF3B6B",
};

export function OrganizationalOptimizerPanel() {
  const [analysis, setAnalysis] = useState<OrganizationalOptimizerResponse | null>(null);
  const [assistant, setAssistant] = useState<OrganizationalAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Which managers are overloaded?");
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson<OrganizationalOptimizerResponse>("/api/organization/optimizer/default");
      if (!isOptimizer(payload)) throw new Error("Malformed organization optimizer payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Organizational optimizer could not load graph analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<OrganizationalOptimizerResponse>("/api/organization/optimizer/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_type: "split_team",
          question: "What happens if Engineering Platform splits into 3 teams?",
          target_team: "Engineering Platform",
          new_team_count: 3,
          horizon_months: 12,
        }),
      });
      if (!isOptimizer(payload)) throw new Error("Malformed organization simulation payload");
      setAnalysis(payload);
    } catch {
      setError("Organizational restructure simulation failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson<OrganizationalAssistantResponse>("/api/organization/optimizer/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, horizon_months: 12 }),
      });
      if (isAssistant(payload)) setAssistant(payload);
    } catch {
      setAssistant({
        model: "Organizational Design Intelligence Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "summary",
        answer: "The organization assistant could not query live graph analytics.",
        confidence: 0,
        citedEvidence: [],
        recommendedActions: [],
        simulation: null,
        sourceSystems: [],
        storage: "",
      });
    } finally {
      setAssistantLoading(false);
    }
  }, [question]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/organization/optimizer/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing organization optimizer stream");
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
            if (!dataLine || Date.now() <= manualScenarioUntil.current) continue;
            const payload = JSON.parse(dataLine.slice(6)) as unknown;
            if (isOptimizer(payload)) {
              setAnalysis(payload);
              setLoading(false);
            }
          }
        }
        setStreamStatus("ready");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("fallback");
      }
    }

    const refreshTimer = window.setTimeout(() => {
      void loadDefault();
      void askAssistant();
    }, 200);
    const streamTimer = window.setTimeout(() => {
      void connectStream();
    }, 7000);
    return () => {
      controller.abort();
      window.clearTimeout(refreshTimer);
      window.clearTimeout(streamTimer);
    };
  }, [askAssistant, loadDefault]);

  const managerChart = useMemo(
    () =>
      analysis?.managerLoad.slice(0, 7).map((manager) => ({
        name: shortName(manager.managerName),
        commandSpan: manager.directReports,
        overload: Math.round(manager.overloadRisk),
        bottleneck: Math.round(manager.leadershipBottleneckScore),
      })) ?? [],
    [analysis],
  );

  const teamChart = useMemo(
    () =>
      analysis?.teamRecommendations.slice(0, 6).map((team) => ({
        name: shortName(team.teamName),
        gain: Math.round(team.expectedProductivityGain),
        latency: Math.round(team.expectedLatencyReduction),
      })) ?? [],
    [analysis],
  );

  const forecastChart = useMemo(
    () =>
      analysis?.forecasts.map((forecast) => ({
        period: forecast.period.replace("_", " "),
        headcount: forecast.projectedHeadcount,
        leaders: forecast.leadershipRolesNeeded,
        restructure: Math.round(forecast.restructureProbability),
      })) ?? [],
    [analysis],
  );

  const graph = useMemo(() => buildGraphView(analysis?.graphNodes ?? [], analysis?.graphEdges ?? []), [analysis]);

  return (
    <section id="organizational-optimizer-panel" data-testid="organizational-optimizer-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Network className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Organizational Structure Optimizer</p>
            <h2 className="text-xl font-semibold text-white">Graph AI org design, reporting load, silos, skill concentration, simulations, and executive recommendations</h2>
            <p className="mt-1 max-w-5xl text-sm leading-6 text-slate-400">
              The optimizer models employees, managers, teams, departments, projects, locations, skills, reporting chains, communication paths, mentorship, and work ownership as an organizational graph.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <button onClick={() => void runSimulation()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <GitBranch className="size-4" />}
            Simulate split
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Building organizational graph, manager load, communication latency, silo risk, skill concentration, simulations, and forecasts...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Org health" value={`${Math.round(analysis.summary.organizationalHealthScore)}%`} />
            <Stat label="Graph nodes" value={String(analysis.summary.graphNodes)} />
            <Stat label="Graph edges" value={String(analysis.summary.graphEdges)} />
            <Stat label="Overloaded mgrs" value={String(analysis.summary.overloadedManagers)} tone="risk" />
            <Stat label="Bottlenecks" value={String(analysis.summary.communicationBottlenecks)} tone="risk" />
            <Stat label="Silos" value={String(analysis.summary.highSiloUnits)} tone="risk" />
            <Stat label="Skill risk" value={String(analysis.summary.criticalSkillConcentrations)} tone="risk" />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 border border-line/70 bg-panel2/65 p-4">
            <div className="flex items-start gap-3">
              <Radio className="mt-1 size-4 text-mint" />
              <p className="text-sm leading-6 text-slate-300">{analysis.executiveBrief}</p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Waypoints} label="Interactive organizational graph" />
              <OrgGraph nodes={graph.nodes} edges={graph.edges} />
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(nodeColor).map(([type, color]) => (
                  <span key={type} className="inline-flex items-center gap-2 text-xs text-slate-400">
                    <span className="size-2" style={{ background: color }} />
                    {type}
                  </span>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={UsersRound} label="Manager load analytics" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={managerChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="commandSpan" fill="#38BDF8" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="overload" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="bottleneck" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={GitBranch} label="Team structure optimization" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={teamChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="gain" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="latency" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={AlertTriangle} label="Future organization forecast" />
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastChart} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="period" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="headcount" stroke="#38BDF8" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="leaders" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="restructure" stroke="#FF3B6B" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <Panel title="Reporting structure analyzer" icon={UsersRound}>
              {analysis.reportingStructure.slice(0, 4).map((item) => (
                <Item key={item.unit} title={item.unit} badge={`${Math.round(item.reportingRisk)}%`} text={`${item.leadershipBottleneck}. ${item.recommendation}`} />
              ))}
            </Panel>

            <Panel title="Communication flow analyzer" icon={MessageSquare}>
              {analysis.communicationFlows.slice(0, 4).map((item) => (
                <Item
                  key={`${item.sourceUnit}-${item.targetUnit}`}
                  title={`${item.sourceUnit} -> ${item.targetUnit}`}
                  badge={`${Math.round(item.delayRisk)}%`}
                  text={`Path length ${item.pathLength}; bottleneck ${item.bottleneckEmployee}. ${item.recommendation}`}
                />
              ))}
            </Panel>

            <Panel title="Silo detection" icon={Network}>
              {analysis.siloRisks.slice(0, 4).map((item) => (
                <Item key={item.unit} title={item.unit} badge={`${Math.round(item.siloRisk)}%`} text={`${item.recommendation} Evidence: ${item.evidence.slice(0, 2).join(" | ")}`} />
              ))}
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <Panel title="Skill distribution risk" icon={Brain}>
              {analysis.skillDistribution.slice(0, 6).map((item) => (
                <Item
                  key={item.skill}
                  title={`${item.skill} / ${item.dominantTeam}`}
                  badge={`${Math.round(item.concentrationRisk)}%`}
                  text={`${item.expertCount} experts. ${item.recommendation}`}
                />
              ))}
            </Panel>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Brain} label="Organizational AI assistant" />
              <div className="flex flex-wrap gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan"
                  placeholder="Ask about bottlenecks, managers, silos, skills, or simulations"
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
                    <span className="text-xs text-mint">{Math.round(assistant.confidence * 100)}% confidence</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-300">{assistant.answer}</p>
                  <div className="mt-3 grid gap-2 md:grid-cols-2">
                    {assistant.recommendedActions.slice(0, 4).map((action) => (
                      <p key={action} className="border border-cyan/20 bg-cyan/10 p-2 text-xs leading-5 text-cyan">{action}</p>
                    ))}
                  </div>
                </div>
              ) : null}
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
            <article className="border border-cyan/25 bg-cyan/10 p-4">
              <SectionTitle icon={GitBranch} label="Restructure simulation" />
              {analysis.simulations.slice(0, 2).map((simulation) => (
                <div key={`${simulation.scenarioType}-${simulation.question}`} className="mb-3 border border-cyan/20 bg-panel/70 p-3 last:mb-0">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <h3 className="text-sm font-semibold text-white">{simulation.question}</h3>
                    <span className="text-sm font-semibold text-cyan">{Math.round(simulation.confidence * 100)}%</span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-300">{simulation.expectedBenefit}</p>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-5">
                    <MiniMetric label="Productivity" value={simulation.productivityImpact} />
                    <MiniMetric label="Comms" value={simulation.communicationImpact} />
                    <MiniMetric label="Cost" value={simulation.costImpact} />
                    <MiniMetric label="Collab" value={simulation.collaborationImpact} />
                    <MiniMetric label="Risk" value={simulation.riskImpact} inverse />
                  </div>
                </div>
              ))}
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={AlertTriangle} label="Executive recommendations" />
              <div className="grid gap-3">
                {analysis.recommendations.slice(0, 5).map((recommendation) => (
                  <RecommendationCard key={recommendation.recommendationId} recommendation={recommendation} />
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function OrgGraph({ nodes, edges }: { nodes: GraphNodeView[]; edges: GraphEdgeView[] }) {
  return (
    <div className="h-80 overflow-hidden border border-line/60 bg-void/50">
      <svg viewBox="0 0 720 320" className="size-full" role="img" aria-label="Organizational relationship graph">
        {edges.map((edge) => (
          <line
            key={`${edge.source.id}-${edge.target.id}-${edge.type}`}
            x1={edge.source.x}
            y1={edge.source.y}
            x2={edge.target.x}
            y2={edge.target.y}
            stroke={edge.risk > 70 ? "#F05D5E" : "#263241"}
            strokeWidth={edge.type === "reports_to" ? 1.8 : 1}
            strokeOpacity={0.85}
          />
        ))}
        {nodes.map((node, nodeIndex) => (
          <g key={`${node.id}-${nodeIndex}`}>
            <circle cx={node.x} cy={node.y} r={node.type === "department" ? 16 : node.type === "team" ? 12 : 9} fill={nodeColor[node.type]} opacity={0.9} />
            <circle cx={node.x} cy={node.y} r={Math.max(11, 8 + node.riskScore / 9)} fill="none" stroke={node.riskScore > 70 ? "#FF3B6B" : "#334155"} strokeOpacity={0.7} />
            <text x={node.x + 13} y={node.y + 4} fill="#CBD5E1" fontSize="10">
              {node.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <SectionTitle icon={Icon} label={title} />
      <div className="grid gap-3">{children}</div>
    </article>
  );
}

function SectionTitle({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Item({ title, badge, text }: { title: string; badge: string; text: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-white">{title}</h3>
        <span className="shrink-0 text-xs text-cyan">{badge}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{text}</p>
    </div>
  );
}

function RecommendationCard({ recommendation }: { recommendation: OrganizationalRecommendation }) {
  return (
    <div className="border-l-2 bg-panel/70 p-3" style={{ borderColor: riskColor[recommendation.priority] }}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-sm font-semibold text-white">{recommendation.action}</h3>
        <span className="text-xs uppercase" style={{ color: riskColor[recommendation.priority] }}>{recommendation.priority}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.reason}</p>
      <p className="mt-2 text-xs leading-5 text-mint">{recommendation.expectedImprovement}</p>
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

function MiniMetric({ label, value, inverse = false }: { label: string; value: number; inverse?: boolean }) {
  const score = inverse ? 100 - value : value;
  const priority = toPriority(score);
  return (
    <div>
      <div className="flex items-center justify-between gap-2 text-slate-500">
        <span>{label}</span>
        <span style={{ color: riskColor[priority] }}>{Math.round(value)}</span>
      </div>
      <div className="mt-1 h-1 bg-black/30">
        <div className="h-full" style={{ width: `${Math.max(4, Math.min(100, Math.abs(value)))}%`, backgroundColor: riskColor[priority] }} />
      </div>
    </div>
  );
}

type GraphNodeView = OrgGraphNode & { x: number; y: number; type: OrgNodeType };
type GraphEdgeView = { source: GraphNodeView; target: GraphNodeView; type: OrgEdgeType; risk: number };

function buildGraphView(nodes: OrgGraphNode[], edges: OrgGraphEdge[]) {
  const priorityTypes: OrgNodeType[] = ["department", "team", "manager", "employee", "project", "skill", "location"];
  const selected = nodes
    .filter((node) => node.nodeType !== "location" || node.riskScore > 0)
    .sort((left, right) => {
      const typeDelta = priorityTypes.indexOf(left.nodeType) - priorityTypes.indexOf(right.nodeType);
      if (typeDelta !== 0) return typeDelta;
      return right.riskScore + right.centrality * 100 - (left.riskScore + left.centrality * 100);
    })
    .slice(0, 26);
  const centerX = 360;
  const centerY = 160;
  const radiusX = 270;
  const radiusY = 115;
  const graphNodes: GraphNodeView[] = selected.map((node, index) => {
    const angle = (index / Math.max(1, selected.length)) * Math.PI * 2 - Math.PI / 2;
    const ring = node.nodeType === "department" ? 0.55 : node.nodeType === "team" ? 0.78 : 1;
    return {
      ...node,
      type: node.nodeType,
      x: centerX + Math.cos(angle) * radiusX * ring,
      y: centerY + Math.sin(angle) * radiusY * ring,
      label: trimLabel(node.label),
    };
  });
  const byId = new Map(graphNodes.map((node) => [node.id, node]));
  const graphEdges: GraphEdgeView[] = [];
  for (const edge of edges) {
    const source = byId.get(edge.source);
    const target = byId.get(edge.target);
    if (source && target) graphEdges.push({ source, target, type: edge.edgeType, risk: edge.risk });
    if (graphEdges.length >= 80) break;
  }
  return { nodes: graphNodes, edges: graphEdges };
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, cache: "no-store" });
  const text = await response.text();
  const payload = text ? (JSON.parse(text) as unknown) : {};
  if (!response.ok) throw new Error("Organization optimizer request failed");
  return payload as T;
}

function isOptimizer(value: unknown): value is OrganizationalOptimizerResponse {
  const candidate = value as Partial<OrganizationalOptimizerResponse> | null;
  return Boolean(
    candidate &&
      typeof candidate.model === "string" &&
      candidate.summary &&
      Array.isArray(candidate.graphNodes) &&
      Array.isArray(candidate.graphEdges) &&
      Array.isArray(candidate.managerLoad) &&
      Array.isArray(candidate.communicationFlows) &&
      Array.isArray(candidate.teamRecommendations) &&
      Array.isArray(candidate.recommendations),
  );
}

function isAssistant(value: unknown): value is OrganizationalAssistantResponse {
  const candidate = value as Partial<OrganizationalAssistantResponse> | null;
  return Boolean(candidate && typeof candidate.answer === "string" && typeof candidate.intent === "string");
}

function toPriority(score: number): OrgRiskLevel {
  if (score >= 82) return "critical";
  if (score >= 64) return "high";
  if (score >= 38) return "medium";
  return "low";
}

function shortName(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .join(" ");
}

function trimLabel(value: string) {
  return value.length > 18 ? `${value.slice(0, 16)}...` : value;
}
