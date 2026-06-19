"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type React from "react";
import {
  Activity,
  BrainCircuit,
  Database,
  Filter,
  GitBranch,
  Loader2,
  MessageSquare,
  Network,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  Workflow,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type {
  BrainComponentStatus,
  BrainNodeType,
  OrganizationalBrainAssistantResponse,
  OrganizationalBrainEdge,
  OrganizationalBrainNode,
  OrganizationalBrainResponse,
} from "@/types/organizational-brain";

const nodeColor: Record<BrainNodeType, string> = {
  employee: "#38BDF8",
  team: "#2EE9D3",
  department: "#A78BFA",
  project: "#7CF0A6",
  skill: "#F6B44B",
  client: "#F05D5E",
  knowledge_asset: "#F472B6",
  location: "#94A3B8",
};

const statusClass: Record<BrainComponentStatus, string> = {
  ready: "border-mint/40 bg-mint/10 text-mint",
  degraded: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
};

const typeOptions: Array<BrainNodeType | "all"> = ["all", "employee", "team", "department", "project", "skill", "client", "knowledge_asset", "location"];

export function OrganizationalBrainPanel() {
  const [brain, setBrain] = useState<OrganizationalBrainResponse | null>(null);
  const [assistant, setAssistant] = useState<OrganizationalBrainAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Who is the most influential employee?");
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<BrainNodeType | "all">("all");
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState("");

  const loadBrain = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/organization/brain/default", { cache: "no-store" });
      if (!response.ok) throw new Error("Organizational Brain failed");
      setBrain((await response.json()) as OrganizationalBrainResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Organizational Brain graph could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    setError("");
    try {
      const response = await fetch("/api/organization/brain/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, horizon_months: 12 }),
      });
      if (!response.ok) throw new Error("Organizational Brain assistant failed");
      setAssistant((await response.json()) as OrganizationalBrainAssistantResponse);
    } catch {
      setError("Organizational Brain assistant could not answer.");
    } finally {
      setAssistantLoading(false);
    }
  }, [question]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadBrain(), 0);
    return () => window.clearTimeout(timer);
  }, [loadBrain]);

  useEffect(() => {
    let source: EventSource | null = null;
    const timer = window.setTimeout(() => {
      source = new EventSource("/api/organization/brain/stream");
      source.addEventListener("organizational_brain", (event) => {
        try {
          setBrain(JSON.parse((event as MessageEvent).data) as OrganizationalBrainResponse);
          setLoading(false);
          setStreamStatus("live");
        } catch {
          setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
        }
      });
      source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    }, 10000);
    return () => {
      window.clearTimeout(timer);
      source?.close();
    };
  }, []);

  const scoreRows = useMemo(
    () =>
      brain
        ? [
            { name: "Brain", score: Math.round(brain.summary.organizationalBrainScore) },
            { name: "Production", score: Math.round(brain.productionReadinessScore) },
            { name: "Research", score: Math.round(brain.researchInnovationScore) },
            { name: "GNN", score: Math.round((1 - brain.gnnEngine.validationMae) * 100) },
            { name: "Graph", score: Math.min(100, Math.round(brain.summary.graphNodes * 0.7 + brain.summary.graphEdges * 0.12)) },
          ]
        : [],
    [brain],
  );

  const riskRows = useMemo(
    () =>
      brain?.riskPredictions.slice(0, 6).map((risk) => ({
        name: risk.riskType.replaceAll("_", " "),
        score: Math.round(risk.riskScore),
        entity: risk.affectedEntity,
      })) ?? [],
    [brain],
  );

  const visibleGraph = useMemo(() => buildVisibleGraph(brain?.graphVisualization.nodes ?? [], brain?.graphVisualization.edges ?? [], search, typeFilter), [brain, search, typeFilter]);

  return (
    <section
      id="organizational-brain-panel"
      data-testid="organizational-brain-panel"
      className="border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-5xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            <span>AI Organizational Brain</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
            {brain ? <span className="border border-mint/30 bg-mint/10 px-2 py-1 text-mint">{brain.finalVerdict}</span> : null}
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">GNN organizational intelligence network</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {brain
              ? brain.executiveBrief
              : "Building the live company graph across employees, teams, departments, projects, clients, skills, knowledge assets, locations, communication paths, dependencies, and influence networks."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void askAssistant()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
          >
            {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <MessageSquare className="size-4" />}
            Ask Graph AI
          </button>
          <button
            type="button"
            onClick={() => void loadBrain()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
        <Metric icon={Network} label="Graph Nodes" value={brain ? String(brain.summary.graphNodes) : "loading"} />
        <Metric icon={GitBranch} label="Graph Edges" value={brain ? String(brain.summary.graphEdges) : "loading"} />
        <Metric icon={BrainCircuit} label="GNN Predictions" value={brain ? String(brain.summary.gnnPredictionCount) : "loading"} />
        <Metric icon={Activity} label="Brain Score" value={brain ? `${Math.round(brain.summary.organizationalBrainScore)}/100` : "loading"} />
        <Metric icon={Database} label="Graph DB" value={brain?.graphDatabase.status ?? "loading"} />
        <Metric icon={Workflow} label="GNN MAE" value={brain ? brain.gnnEngine.validationMae.toFixed(3) : "loading"} />
        <Metric icon={ShieldCheck} label="Production" value={brain ? `${Math.round(brain.productionReadinessScore)}/100` : "loading"} />
        <Metric icon={Filter} label="Research" value={brain ? `${Math.round(brain.researchInnovationScore)}/100` : "loading"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <Panel title="Interactive Company Graph" icon={Network}>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <div className="flex h-10 min-w-64 items-center gap-2 border border-line bg-void/40 px-3 text-sm text-slate-300">
              <Search className="size-4 text-slate-500" />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search graph"
                className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
              />
            </div>
            <select
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value as BrainNodeType | "all")}
              className="h-10 border border-line bg-panel2 px-3 text-sm text-slate-200 outline-none"
            >
              {typeOptions.map((type) => (
                <option key={type} value={type}>
                  {type.replace("_", " ")}
                </option>
              ))}
            </select>
            <button
              type="button"
              aria-label="Zoom in organizational brain graph"
              title="Zoom in"
              onClick={() => setZoom((value) => Math.min(1.8, value + 0.12))}
              className="grid size-10 place-items-center border border-line bg-panel2 text-slate-200"
            >
              <ZoomIn className="size-4" />
            </button>
            <button
              type="button"
              aria-label="Zoom out organizational brain graph"
              title="Zoom out"
              onClick={() => setZoom((value) => Math.max(0.7, value - 0.12))}
              className="grid size-10 place-items-center border border-line bg-panel2 text-slate-200"
            >
              <ZoomOut className="size-4" />
            </button>
          </div>
          <div className="h-[440px] overflow-hidden border border-line bg-void/35">
            <svg data-testid="organizational-brain-graph" viewBox={`0 0 ${760 / zoom} ${560 / zoom}`} className="h-full w-full">
              <rect x="0" y="0" width="760" height="560" fill="#050B13" />
              {visibleGraph.edges.map((edge, index) => {
                const source = visibleGraph.nodeMap.get(edge.source);
                const target = visibleGraph.nodeMap.get(edge.target);
                if (!source || !target) return null;
                return (
                  <line
                    key={`${edge.source}-${edge.target}-${edge.edgeType}-${index}`}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke={edge.riskScore >= 60 ? "#F05D5E" : "#223044"}
                    strokeWidth={Math.max(1, edge.weight * 1.7)}
                    opacity={edge.edgeType === "communicates_with" ? 0.82 : 0.42}
                  />
                );
              })}
              {visibleGraph.nodes.map((node, index) => (
                <g key={`${node.id}-${index}`}>
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={node.nodeType === "employee" ? Math.max(4, 5 + node.influenceScore / 24) : 7}
                    fill={nodeColor[node.nodeType]}
                    opacity={0.94}
                    stroke={node.riskScore >= 65 ? "#FF3B6B" : "#E2E8F0"}
                    strokeWidth={node.riskScore >= 65 ? 2 : 0.6}
                  />
                  <text x={node.x + 8} y={node.y + 4} fill="#CBD5E1" fontSize="9">
                    {node.label.length > 18 ? `${node.label.slice(0, 18)}...` : node.label}
                  </text>
                </g>
              ))}
            </svg>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            {typeOptions.filter((type): type is BrainNodeType => type !== "all").map((type) => (
              <span key={type} className="inline-flex items-center gap-2 border border-line bg-panel2 px-2 py-1 text-xs text-slate-300">
                <span className="size-2" style={{ backgroundColor: nodeColor[type] }} />
                {type.replace("_", " ")}
              </span>
            ))}
          </div>
        </Panel>

        <div className="grid gap-4">
          <Panel title="GNN Engine" icon={BrainCircuit}>
            <div className="grid gap-2 text-sm text-slate-300">
              <div className="flex justify-between gap-4 border border-line bg-void/30 px-3 py-2">
                <span>Models</span>
                <span className="text-cyan">{brain?.gnnEngine.supportedModels.join(" + ") ?? "loading"}</span>
              </div>
              <div className="flex justify-between gap-4 border border-line bg-void/30 px-3 py-2">
                <span>Inference</span>
                <span className="text-mint">{brain ? `${brain.gnnEngine.inferenceLatencyMs.toFixed(1)}ms` : "loading"}</span>
              </div>
              <div className="flex justify-between gap-4 border border-line bg-void/30 px-3 py-2">
                <span>Embeddings</span>
                <span className="text-white">{brain ? `${brain.gnnEngine.embeddings.length} visible / ${brain.gnnEngine.trainingNodes} trained nodes` : "loading"}</span>
              </div>
              <p className="text-xs leading-5 text-slate-500">{brain?.gnnEngine.trainingStatus ?? "Training and inference status loading."}</p>
            </div>
          </Panel>

          <Panel title="Ask Organizational Brain" icon={MessageSquare}>
            <div className="flex gap-2">
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="h-10 min-w-0 flex-1 border border-line bg-void/40 px-3 text-sm text-white outline-none placeholder:text-slate-500"
              />
              <button
                type="button"
                aria-label="Ask organizational brain"
                title="Ask organizational brain"
                onClick={() => void askAssistant()}
                className="grid h-10 w-12 place-items-center border border-cyan/40 bg-cyan/10 text-cyan"
              >
                {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              </button>
            </div>
            {assistant ? (
              <div className="mt-3 border border-cyan/25 bg-cyan/5 p-3">
                <div className="flex flex-wrap gap-2 text-xs uppercase text-cyan">
                  <span>{assistant.intent}</span>
                  <span>{Math.round(assistant.confidence * 100)}% confidence</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-white">{assistant.answer}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {assistant.recommendedActions.slice(0, 2).map((action) => (
                    <span key={action} className="border border-line bg-void/40 px-2 py-1 text-xs text-slate-300">{action}</span>
                  ))}
                </div>
              </div>
            ) : null}
          </Panel>
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Readiness Scorecard" icon={ShieldCheck}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 8, right: 12, top: 8, bottom: 8 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" width={86} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                  {scoreRows.map((row, index) => (
                    <Cell key={row.name} fill={["#2EE9D3", "#7CF0A6", "#A78BFA", "#38BDF8", "#F6B44B"][index % 5]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Risk Predictions" icon={Activity}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskRows} margin={{ left: 0, right: 12, top: 8, bottom: 36 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} angle={-22} textAnchor="end" interval={0} />
                <YAxis domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="score" fill="#F05D5E" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Components" icon={Workflow}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {brain?.components.map((component) => (
              <div key={component.name} className="border border-line bg-void/30 p-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-medium text-white">{component.name}</p>
                  <span className={`border px-2 py-1 text-xs ${statusClass[component.status]}`}>{component.status}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{component.evidence.join(" | ")}</p>
              </div>
            )) ?? <p className="text-sm text-slate-500">Component status loading.</p>}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <FindingList title="Communication Flow" icon={Network} rows={brain?.communicationFlow.slice(0, 4).map((item) => [`${item.sourceUnit} -> ${item.targetUnit}`, `${Math.round(item.delayRisk)}% delay risk`, item.recommendation]) ?? []} />
        <FindingList title="Knowledge Flow" icon={Database} rows={brain?.knowledgeFlow.slice(0, 4).map((item) => [item.knowledgeAsset, `${Math.round(item.knowledgeLossRisk)}% loss risk`, item.recommendation]) ?? []} />
        <FindingList title="Influence Network" icon={BrainCircuit} rows={brain?.influenceNetwork.slice(0, 4).map((item) => [item.employeeName, `${Math.round(item.influenceScore)}% influence`, item.hiddenLeader ? "Hidden leader signal" : item.formalRole]) ?? []} />
      </div>
    </section>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="border border-line bg-panel2/70 p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <p className="mt-2 text-xl font-semibold text-white">{value}</p>
    </div>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <div className="border border-line bg-panel2/65 p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-white">
        <Icon className="size-4 text-cyan" />
        <span>{title}</span>
      </div>
      {children}
    </div>
  );
}

function FindingList({ title, icon, rows }: { title: string; icon: LucideIcon; rows: string[][] }) {
  return (
    <Panel title={title} icon={icon}>
      <div className="grid gap-2">
        {rows.length ? rows.map(([name, score, detail]) => (
          <div key={`${title}-${name}`} className="border border-line bg-void/30 p-3">
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-medium text-white">{name}</p>
              <span className="shrink-0 text-xs text-cyan">{score}</span>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-500">{detail}</p>
          </div>
        )) : <p className="text-sm text-slate-500">Loading graph findings.</p>}
      </div>
    </Panel>
  );
}

function buildVisibleGraph(nodes: OrganizationalBrainNode[], edges: OrganizationalBrainEdge[], search: string, typeFilter: BrainNodeType | "all") {
  const normalized = search.trim().toLowerCase();
  const visibleNodes = nodes
    .filter((node) => typeFilter === "all" || node.nodeType === typeFilter)
    .filter((node) => !normalized || node.label.toLowerCase().includes(normalized) || node.id.toLowerCase().includes(normalized) || node.team?.toLowerCase().includes(normalized))
    .sort((a, b) => b.influenceScore + b.riskScore + b.knowledgeScore - (a.influenceScore + a.riskScore + a.knowledgeScore))
    .slice(0, 80);
  const nodeMap = new Map(visibleNodes.map((node) => [node.id, node]));
  const visibleEdges = edges.filter((edge) => nodeMap.has(edge.source) && nodeMap.has(edge.target)).slice(0, 180);
  return { nodes: visibleNodes, edges: visibleEdges, nodeMap };
}
