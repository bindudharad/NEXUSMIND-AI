"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Bot,
  CalendarClock,
  CheckCircle2,
  GitBranch,
  Loader2,
  Radio,
  RefreshCw,
  Route,
  Send,
  ShieldAlert,
  Users,
  Workflow,
} from "lucide-react";

import type { AutonomousWorkflowResponse, OperationsAssistantResponse, WorkflowPriority } from "@/types/autonomous-workflow";

const priorityColor: Record<WorkflowPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function AutonomousWorkflowPanel() {
  const [workflow, setWorkflow] = useState<AutonomousWorkflowResponse | null>(null);
  const [assistant, setAssistant] = useState<OperationsAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Assign this task.");
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
      const payload = await fetchJson("/api/workflows/autonomous/default", { cache: "no-store" });
      if (!isAutonomousWorkflow(payload)) throw new Error("Malformed autonomous workflow payload");
      setWorkflow(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Autonomous Workflow Automation could not refresh live operations intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runMode = useCallback(async (mode: "pressure" | "crisis") => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/workflows/autonomous/run",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode, realtime: true }),
          cache: "no-store",
        },
        60000,
      );
      if (!isAutonomousWorkflow(payload)) throw new Error("Malformed autonomous workflow payload");
      setWorkflow(payload);
    } catch {
      setError("Autonomous Workflow Automation could not process the requested scenario.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson(
        "/api/workflows/autonomous/assistant",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
          cache: "no-store",
        },
        60000,
      );
      if (!isOperationsAssistant(payload)) throw new Error("Malformed operations assistant payload");
      setAssistant(payload);
    } catch {
      setAssistant({
        model: "AI Operations Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "error",
        answer: "Operations assistant could not produce an action from the live API.",
        triggeredActions: [],
        citedWorkflows: [],
        recommendedActions: [],
        confidence: 0,
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
      let streamStarted = false;
      const fallback = window.setTimeout(() => {
        if (!streamStarted && !controller.signal.aborted) setStreamStatus("polling");
      }, 12000);
      try {
        const response = await fetch("/api/workflows/autonomous/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Autonomous Workflow stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing Autonomous Workflow stream");
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
            if (isAutonomousWorkflow(payload) && Date.now() > manualScenarioUntil.current) {
              setWorkflow(payload);
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
    }, 3000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadDefault]);

  const assignmentData = useMemo(
    () =>
      workflow?.taskAssignments.slice(0, 6).map((item) => ({
        task: shortLabel(item.taskTitle),
        score: Math.round(item.assignmentScore),
        delivery: Math.round(item.deliverySuccessProbability),
      })) ?? [],
    [workflow],
  );

  const workloadData = useMemo(
    () =>
      workflow?.workloadBalancing.map((item) => ({
        name: shortLabel(item.fromEmployee),
        reduction: Math.round(item.burnoutRiskReduction),
        hours: item.hours,
      })) ?? [],
    [workflow],
  );

  const approvalData = useMemo(() => {
    const approvals = workflow?.approvalDecisions ?? [];
    return [
      { name: "Approved", value: approvals.filter((item) => item.decision === "approved").length, fill: "#7CF0A6" },
      { name: "Review", value: approvals.filter((item) => item.decision === "needs_review").length, fill: "#F6B44B" },
      { name: "Rejected", value: approvals.filter((item) => item.decision === "rejected").length, fill: "#F05D5E" },
    ].filter((item) => item.value > 0);
  }, [workflow]);

  return (
    <article className="border border-cyan/20 bg-panel/85 p-5 shadow-control backdrop-blur" data-testid="autonomous-workflow-panel">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-3xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Workflow className="size-4" />
            <span>Autonomous Workflow Automation</span>
            <span className="inline-flex items-center gap-1 text-mint">
              <Radio className="size-3" />
              {streamStatus}
            </span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Virtual operations manager AI</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Task assignment, approvals, scheduling, reminders, workload balancing, escalation routing, and multi-agent coordination run from live operating signals.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={loadDefault} type="button">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
          <button className="border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={() => void runMode("pressure")} type="button">
            Balance workloads
          </button>
          <button className="border border-line bg-panel2 px-3 py-2 text-sm text-white hover:border-cyan/60" onClick={() => void runMode("crisis")} type="button">
            Escalate risks
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-200">{error}</p> : null}
      {loading && !workflow ? <p className="mt-5 text-sm text-slate-400">Building autonomous operations plan...</p> : null}

      {workflow ? (
        <>
          <section className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-6">
            <Metric label="Active workflows" value={String(workflow.summary.activeWorkflows)} />
            <Metric label="Approvals" value={String(workflow.summary.pendingApprovals)} />
            <Metric label="Meetings" value={String(workflow.summary.scheduledMeetings)} />
            <Metric label="Reminders" value={String(workflow.summary.remindersCreated)} />
            <Metric label="Escalations" value={String(workflow.summary.escalationsOpen)} />
            <Metric label="Readiness" value={`${workflow.summary.operationsReadinessScore}/100`} />
          </section>

          <section className="mt-5 grid gap-4 xl:grid-cols-[1.25fr_0.85fr]">
            <ChartBlock title="Task assignment confidence">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={assignmentData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="task" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Bar dataKey="score" fill="#1D9BF0" />
                  <Bar dataKey="delivery" fill="#7CF0A6" />
                </BarChart>
              </ResponsiveContainer>
            </ChartBlock>

            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
                <CheckCircle2 className="size-4 text-cyan" />
                <span>Pending approvals</span>
              </div>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={approvalData} dataKey="value" nameKey="name" innerRadius={38} outerRadius={62} paddingAngle={3}>
                      {approvalData.map((item) => (
                        <Cell key={item.name} fill={item.fill} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="space-y-2">
                {workflow.approvalDecisions.slice(0, 3).map((item) => (
                  <div key={item.requestId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm text-white">{item.requesterName}</span>
                      <span className="text-xs uppercase text-slate-400">{item.decision.replace("_", " ")}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.rationale}</p>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-3">
            <ListBlock icon={CalendarClock} title="Upcoming meetings">
              {workflow.meetingSchedules.slice(0, 4).map((item) => (
                <Item key={item.meetingId} title={item.title} badge={item.scheduledTime} text={item.rationale} />
              ))}
            </ListBlock>

            <ListBlock icon={Route} title="Workload distribution">
              {workflow.workloadBalancing.slice(0, 4).map((item) => (
                <Item key={item.actionId} title={`${item.fromEmployee} -> ${item.toEmployee}`} badge={`${item.hours}h`} text={item.rationale} />
              ))}
            </ListBlock>

            <ListBlock icon={ShieldAlert} title="Escalations">
              {workflow.escalations.slice(0, 4).map((item) => (
                <Item key={item.escalationId} title={item.title} badge={item.severity} text={`${item.owner}: ${item.rationale}`} priority={item.severity} />
              ))}
            </ListBlock>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="border border-line/70 bg-void/35 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
                <GitBranch className="size-4 text-cyan" />
                <span>Automation events and agents</span>
              </div>
              <div className="grid gap-3 xl:grid-cols-2">
                <div className="space-y-2">
                  {workflow.automationEvents.slice(0, 5).map((item) => (
                    <Item key={item.eventId} title={item.trigger.replaceAll("_", " ")} badge={item.severity} text={item.action} priority={item.severity} />
                  ))}
                </div>
                <div className="space-y-2">
                  {workflow.agentActions.slice(0, 5).map((item) => (
                    <Item key={item.agent} title={item.agent} badge={`${Math.round(item.confidence * 100)}%`} text={item.action} />
                  ))}
                </div>
              </div>
            </div>

            <div className="border border-cyan/20 bg-panel2/60 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Bot className="size-4" />
                <span>AI Operations Assistant</span>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  className="min-h-10 flex-1 border border-line bg-void/80 px-3 text-sm text-white outline-none focus:border-cyan/60"
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") void askAssistant();
                  }}
                  value={question}
                />
                <button className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-4 py-2 text-sm text-white hover:bg-cyan/15" onClick={askAssistant} type="button">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              <div className="mt-4 border border-line/60 bg-void/50 p-3">
                <p className="text-sm leading-6 text-slate-200">
                  {assistant?.answer ?? workflow.recommendations[0]?.action ?? "Operations assistant is ready to trigger workflow actions."}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {(assistant?.triggeredActions ?? workflow.sourceSystems.slice(0, 5)).map((item) => (
                    <span key={item} className="border border-line/60 bg-panel px-2 py-1 text-xs text-slate-400">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="mt-4 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
            <ChartBlock title="Burnout reduction from balancing">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={workloadData}>
                  <CartesianGrid stroke="#233047" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={10} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1f2a44", color: "#e2e8f0" }} />
                  <Bar dataKey="reduction" fill="#7CF0A6" />
                  <Bar dataKey="hours" fill="#1D9BF0" />
                </BarChart>
              </ResponsiveContainer>
            </ChartBlock>

            <ListBlock icon={Users} title="Executive recommendations">
              {workflow.recommendations.slice(0, 5).map((item) => (
                <Item key={`${item.category}-${item.title}`} title={item.title} badge={item.priority} text={`${item.action} ${item.expectedImpact}`} priority={item.priority} />
              ))}
            </ListBlock>
          </section>
        </>
      ) : null}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-void/40 p-3">
      <span className="text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-2 block text-xl font-semibold text-white">{value}</strong>
    </div>
  );
}

function ChartBlock({ children, title }: { children: React.ReactNode; title: string }) {
  return (
    <div className="h-72 border border-line/70 bg-void/35 p-4">
      <span className="mb-3 block text-xs uppercase text-slate-500">{title}</span>
      <div className="h-56">{children}</div>
    </div>
  );
}

function ListBlock({
  children,
  icon: Icon,
  title,
}: {
  children: React.ReactNode;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
}) {
  return (
    <div className="border border-line/70 bg-void/35 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="size-4 text-cyan" />
        <span>{title}</span>
      </div>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Item({ badge, priority, text, title }: { badge: string; priority?: WorkflowPriority; text: string; title: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-white">{title}</span>
        <span className="text-xs uppercase" style={{ color: priority ? priorityColor[priority] : "#94a3b8" }}>
          {badge}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{text}</p>
    </div>
  );
}

async function fetchJson(path: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isAutonomousWorkflow(value: unknown): value is AutonomousWorkflowResponse {
  return Boolean(value && typeof value === "object" && "summary" in value && "taskAssignments" in value && Array.isArray((value as AutonomousWorkflowResponse).taskAssignments));
}

function isOperationsAssistant(value: unknown): value is OperationsAssistantResponse {
  return Boolean(value && typeof value === "object" && "answer" in value && "triggeredActions" in value);
}

function shortLabel(value: string) {
  return value.replace(/\b(Backend|Executive|Kubernetes|Reliability|Automation|Engineer)\b/g, "").trim().slice(0, 14);
}
