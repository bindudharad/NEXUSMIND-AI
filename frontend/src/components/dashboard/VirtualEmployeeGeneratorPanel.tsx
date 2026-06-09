"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import {
  Area,
  AreaChart,
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
  BriefcaseBusiness,
  GitBranch,
  Loader2,
  Network,
  Radio,
  RefreshCw,
  Send,
  Sparkles,
  UserPlus,
  Users,
  Workflow,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  StressPropagationEdge,
  TeamInteractionResult,
  VirtualEmployeeAgent,
  VirtualEmployeeRiskLevel,
  VirtualWorkforceAssistantResponse,
  VirtualWorkforceResponse,
} from "@/types/virtual-employee";

const riskTone: Record<VirtualEmployeeRiskLevel, string> = {
  low: "border-mint/30 bg-mint/10 text-mint",
  medium: "border-amber/30 bg-amber/10 text-amber",
  high: "border-orange-400/30 bg-orange-400/10 text-orange-300",
  critical: "border-rose/30 bg-rose/10 text-rose",
};

export function VirtualEmployeeGeneratorPanel() {
  const [analysis, setAnalysis] = useState<VirtualWorkforceResponse | null>(null);
  const [assistant, setAssistant] = useState<VirtualWorkforceAssistantResponse | null>(null);
  const [question, setQuestion] = useState("What happens if we hire 5 engineers?");
  const [employeeCount, setEmployeeCount] = useState(18);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState("");
  const manualUpdateUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = 0;
    try {
      const payload = await fetchJson<VirtualWorkforceResponse>("/api/workforce/virtual-employees/default");
      if (!isWorkforce(payload)) throw new Error("Malformed virtual workforce payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Synthetic Workforce Twin Generator could not load live enterprise simulation.");
    } finally {
      setLoading(false);
    }
  }, []);

  const generateEmployees = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<VirtualWorkforceResponse>("/api/workforce/virtual-employees/generate", {
        method: "POST",
        body: JSON.stringify({
          count: employeeCount,
          department: "AI Platform",
          role_family: "Data Science",
          experience_mix: "senior_heavy",
          seed: 9090 + employeeCount,
        }),
      });
      if (!isWorkforce(payload)) throw new Error("Malformed generation payload");
      setAnalysis(payload);
    } catch {
      setError("Virtual employee generation failed.");
    } finally {
      setLoading(false);
    }
  }, [employeeCount]);

  const simulate = useCallback(async (scenario: "stress" | "hiring" | "leadership") => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = Date.now() + 30000;
    const payloadByScenario = {
      stress: {
        question: "Show stress propagation across Engineering.",
        scenario_type: "stress_propagation",
        employee_count: 18,
        workload_delta_percent: 45,
        resignation_count: 2,
        horizon_weeks: 12,
        seed: 3030,
      },
      hiring: {
        question: "Simulate hiring 5 engineers.",
        scenario_type: "hiring_impact",
        employee_count: 18,
        hiring_count: 5,
        workload_delta_percent: 20,
        horizon_weeks: 12,
        seed: 4040,
      },
      leadership: {
        question: "Simulate a new supportive team lead.",
        scenario_type: "leadership_change",
        employee_count: 18,
        manager_count: 1,
        leadership_style: "supportive",
        workload_delta_percent: 8,
        horizon_weeks: 12,
        seed: 5050,
      },
    } as const;
    try {
      const payload = await fetchJson<VirtualWorkforceResponse>("/api/workforce/virtual-employees/simulate", {
        method: "POST",
        body: JSON.stringify(payloadByScenario[scenario]),
      });
      if (!isWorkforce(payload)) throw new Error("Malformed simulation payload");
      setAnalysis(payload);
    } catch {
      setError("Agent-based workforce simulation failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAsking(true);
    setError("");
    try {
      const payload = await fetchJson<VirtualWorkforceAssistantResponse>("/api/workforce/virtual-employees/ask", {
        method: "POST",
        body: JSON.stringify({ question, horizon_weeks: 12 }),
      });
      if (payload?.simulation) {
        setAssistant(payload);
        setAnalysis(payload.simulation);
      }
    } catch {
      setError("Virtual workforce assistant failed.");
    } finally {
      setAsking(false);
    }
  }, [question]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/workforce/virtual-employees/stream");
    source.addEventListener("virtual_employee_workforce", (event) => {
      if (Date.now() < manualUpdateUntil.current) return;
      try {
        const payload = JSON.parse((event as MessageEvent).data) as VirtualWorkforceResponse;
        if (isWorkforce(payload)) {
          setAnalysis(payload);
          setStreamStatus("live");
        }
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const forecast = analysis?.forecast ?? [];
  const impactData = useMemo(
    () =>
      analysis?.impactMetrics.map((item) => ({
        metric: item.metric,
        baseline: Math.round(item.baseline),
        projected: Math.round(item.projected),
      })) ?? [],
    [analysis],
  );
  const employeeSample = analysis?.virtualEmployees.slice(0, 6) ?? [];
  const topEdges = analysis?.stressPropagation.slice(0, 6) ?? [];

  return (
    <section
      id="virtual-employee-generator-panel"
      data-testid="virtual-employee-generator-panel"
      className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Users className="size-4" />
            <span>Synthetic Workforce Twin Generator</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Agent-based workforce simulation system</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {analysis?.assistantSummary ??
              "Generating synthetic workforce twins with skills, Big Five personality traits, behavior models, stress propagation, team interaction, and project outcome simulation."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void loadDefault()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
          <button
            type="button"
            onClick={() => void simulate("stress")}
            className="inline-flex h-10 items-center gap-2 border border-rose/35 bg-rose/10 px-3 text-sm text-rose transition hover:border-rose"
          >
            <Zap className="size-4" />
            Stress
          </button>
          <button
            type="button"
            onClick={() => void simulate("hiring")}
            className="inline-flex h-10 items-center gap-2 border border-mint/35 bg-mint/10 px-3 text-sm text-mint transition hover:border-mint"
          >
            <UserPlus className="size-4" />
            Hiring
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <Metric icon={Users} label="Synthetic twins" value={analysis ? String(analysis.summary.generatedEmployees) : "verifying"} />
        <Metric icon={Brain} label="Productivity" value={analysis ? `${Math.round(analysis.summary.averageProductivity)}%` : "verifying"} />
        <Metric icon={Zap} label="Stress" value={analysis ? `${Math.round(analysis.summary.averageStress)}%` : "verifying"} />
        <Metric icon={BriefcaseBusiness} label="Delivery" value={analysis ? `${Math.round(analysis.summary.deliveryConfidence)}%` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Scenario Builder" icon={Workflow}>
          <div className="grid gap-3 md:grid-cols-[0.5fr_1fr_auto]">
            <label className="grid gap-1 text-xs uppercase text-slate-500">
              Workforce twins
              <input
                type="number"
                value={employeeCount}
                min={4}
                max={80}
                onChange={(event) => setEmployeeCount(Number(event.target.value))}
                className="h-10 border border-line bg-void px-3 text-sm text-white outline-none focus:border-cyan/60"
              />
            </label>
            <label className="grid gap-1 text-xs uppercase text-slate-500">
              Assistant question
              <input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="h-10 min-w-0 border border-line bg-void px-3 text-sm text-white outline-none focus:border-cyan/60"
                aria-label="Virtual workforce assistant question"
              />
            </label>
            <div className="grid grid-cols-2 gap-2 self-end">
              <button
                type="button"
                onClick={() => void generateEmployees()}
                className="inline-flex h-10 items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-3 text-sm text-cyan"
              >
                <Sparkles className="size-4" />
                Generate
              </button>
              <button
                type="button"
                onClick={() => void askAssistant()}
                className="inline-flex h-10 items-center justify-center gap-2 border border-mint/40 bg-mint/10 px-3 text-sm text-mint"
              >
                {asking ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                Ask
              </button>
            </div>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            <ActionButton icon={UserPlus} label="Hire 5" onClick={() => void simulate("hiring")} />
            <ActionButton icon={GitBranch} label="New Lead" onClick={() => void simulate("leadership")} />
            <ActionButton icon={Zap} label="Stress Map" onClick={() => void simulate("stress")} />
          </div>
          <div className="mt-3 border border-line/70 bg-void/35 p-3">
            <div className="text-xs uppercase text-cyan">{assistant?.intent ?? analysis?.scenario.scenarioType ?? "baseline"}</div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              {assistant?.answer ?? analysis?.projectOutcome.explanation ?? "Simulation output will appear here."}
            </p>
          </div>
        </Panel>

        <Panel title="Forecast Timeline" icon={Radio}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={forecast}>
                <CartesianGrid stroke="#1C2B3A" vertical={false} />
                <XAxis dataKey="week" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Line type="monotone" dataKey="productivity" stroke="#7CF0A6" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="stress" stroke="#FB7185" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="deliveryConfidence" stroke="#2DD4BF" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Synthetic Workforce Twin Agents" icon={Network}>
          <div className="grid gap-2 md:grid-cols-2">
            {employeeSample.map((employee) => (
              <EmployeeCard key={employee.identity.employeeId} employee={employee} />
            ))}
          </div>
        </Panel>

        <Panel title="Impact Model" icon={Brain}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={impactData}>
                <CartesianGrid stroke="#1C2B3A" vertical={false} />
                <XAxis dataKey="metric" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="baseline" fill="#334155" radius={[3, 3, 0, 0]} />
                <Bar dataKey="projected" fill="#2DD4BF" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <MiniMetric label="Delay Weeks" value={analysis ? analysis.projectOutcome.deliveryDelayWeeks.toFixed(1) : "verifying"} />
            <MiniMetric label="Quality" value={analysis ? `${Math.round(analysis.projectOutcome.qualityScore)}%` : "verifying"} />
            <MiniMetric label="Resource Risk" value={analysis ? `${Math.round(analysis.projectOutcome.resourceRisk)}%` : "verifying"} />
            <MiniMetric label="Readiness" value={analysis ? `${Math.round(analysis.summary.readinessScore)}%` : "verifying"} />
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Team Interaction" icon={Users}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {(analysis?.teamInteractions ?? []).map((team) => (
              <TeamCard key={team.teamName} team={team} />
            ))}
          </div>
        </Panel>

        <Panel title="Stress Propagation" icon={GitBranch}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {topEdges.map((edge, index) => (
              <StressEdgeCard key={`${edge.sourceEmployeeId}-${edge.targetEmployeeId}-${index}`} edge={edge} />
            ))}
          </div>
        </Panel>

        <Panel title="AI Recommendations" icon={Sparkles}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {(analysis?.recommendations ?? []).map((item) => (
              <div key={`${item.ownerAgent}-${item.action}`} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <span className="text-sm font-semibold text-white">{item.ownerAgent}</span>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${riskTone[item.priority]}`}>{item.priority}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.action}</p>
                <p className="mt-1 text-[11px] leading-4 text-slate-500">{item.expectedImpact}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Panel title="Behavior Distribution" icon={Zap}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={forecast}>
                <CartesianGrid stroke="#1C2B3A" vertical={false} />
                <XAxis dataKey="week" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Area type="monotone" dataKey="burnoutRisk" stroke="#FB7185" fill="#FB718533" />
                <Area type="monotone" dataKey="collaboration" stroke="#7CF0A6" fill="#7CF0A633" />
                <Area type="monotone" dataKey="attritionRisk" stroke="#F6B44B" fill="#F6B44B33" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Integration Evidence" icon={BriefcaseBusiness}>
          <div className="grid gap-2">
            {(analysis?.integrationEvidence ?? []).map((item) => (
              <div key={item} className="border border-line/60 bg-panel2/45 px-3 py-2 text-xs leading-5 text-slate-400">
                {item}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </section>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/55 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
        <Icon className="size-4" />
        <span>{title}</span>
      </div>
      {children}
    </article>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/60 p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block text-2xl font-semibold text-white">{value}</strong>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/60 bg-panel/50 p-2">
      <span className="text-[10px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{value}</strong>
    </div>
  );
}

function ActionButton({ icon: Icon, label, onClick }: { icon: LucideIcon; label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-10 items-center justify-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
    >
      <Icon className="size-4 text-cyan" />
      {label}
    </button>
  );
}

function EmployeeCard({ employee }: { employee: VirtualEmployeeAgent }) {
  const skills = Object.entries(employee.skills.technicalSkills).slice(0, 3);
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-white">{employee.identity.name}</h3>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            {employee.identity.role} - {employee.personality.introversionExtroversion}
          </p>
        </div>
        <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-[10px] uppercase text-cyan">
          {employee.identity.experienceLevel}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2">
        <MiniMetric label="Prod" value={`${Math.round(employee.behavior.productivityScore)}%`} />
        <MiniMetric label="Stress" value={`${Math.round(employee.behavior.stressLevel)}%`} />
        <MiniMetric label="Collab" value={`${Math.round(employee.behavior.collaboration)}%`} />
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {skills.map(([skill, value]) => (
          <span key={skill} className="border border-line/60 bg-panel2/60 px-2 py-1 text-[10px] text-slate-400">
            {skill} {Math.round(value)}%
          </span>
        ))}
      </div>
    </div>
  );
}

function TeamCard({ team }: { team: TeamInteractionResult }) {
  return (
    <div className="border border-line/60 bg-void/35 p-3">
      <div className="flex items-start justify-between gap-3">
        <span className="text-sm font-semibold text-white">{team.teamName}</span>
        <span className="text-[10px] uppercase text-amber">{Math.round(team.conflictRisk)}% conflict</span>
      </div>
      <div className="mt-2 grid grid-cols-3 gap-2">
        <MiniMetric label="Cohesion" value={`${Math.round(team.cohesionScore)}%`} />
        <MiniMetric label="Knowledge" value={`${Math.round(team.knowledgeSharingScore)}%`} />
        <MiniMetric label="Lead" value={`${Math.round(team.leadershipStability)}%`} />
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{team.explanation}</p>
    </div>
  );
}

function StressEdgeCard({ edge }: { edge: StressPropagationEdge }) {
  const positive = edge.stressTransfer >= 0;
  return (
    <div className="border border-line/60 bg-panel2/45 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-semibold text-white">{edge.relationship.replaceAll("_", " ")}</span>
        <span className={positive ? "text-xs text-rose" : "text-xs text-mint"}>
          {positive ? "+" : ""}
          {edge.stressTransfer.toFixed(1)}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{edge.reason}</p>
    </div>
  );
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: init?.body ? { "Content-Type": "application/json", ...(init.headers ?? {}) } : init?.headers,
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Request failed: ${url}`);
  return (await response.json()) as T;
}

function isWorkforce(value: unknown): value is VirtualWorkforceResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "summary" in value &&
      Array.isArray((value as VirtualWorkforceResponse).virtualEmployees) &&
      Array.isArray((value as VirtualWorkforceResponse).forecast),
  );
}
