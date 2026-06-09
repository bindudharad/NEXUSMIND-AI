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
  Bot,
  Brain,
  Cable,
  CheckCircle2,
  Cpu,
  GitBranch,
  Loader2,
  MessageSquare,
  Network,
  Play,
  Radio,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

import type {
  AgentBoardroomStage,
  AgentCouncilConsensus,
  AgentCouncilResponse,
  AgentConsensusVote,
  AgentDebateExchange,
  AgentName,
  AgentReasoningTrace,
  AgentResearchMetrics,
  AgentRiskLevel,
  AgentSimulationResult,
  AgentWorkflow,
  MultiAgentWorkforceResponse,
} from "@/types/multi-agent-workforce";

const riskTone: Record<AgentRiskLevel, string> = {
  low: "border-mint/30 bg-mint/10 text-mint",
  medium: "border-amber/30 bg-amber/10 text-amber",
  high: "border-orange-400/30 bg-orange-400/10 text-orange-300",
  critical: "border-rose/30 bg-rose/10 text-rose",
};

const agentAccent: Record<AgentName, string> = {
  "HR Agent": "#F472B6",
  "Finance Agent": "#7CF0A6",
  "Security Agent": "#60A5FA",
  "Project Agent": "#F6B44B",
  "Productivity Agent": "#2DD4BF",
  "Client Agent": "#A78BFA",
  "Knowledge Agent": "#CBD5E1",
  "Executive Agent": "#FF3B6B",
};

const voteTone: Record<AgentConsensusVote["vote"], string> = {
  support: "border-mint/25 bg-mint/10 text-mint",
  conditional_support: "border-amber/25 bg-amber/10 text-amber",
  oppose: "border-rose/25 bg-rose/10 text-rose",
};

const BOARDROOM_DEMO_QUESTION = "What if 30 engineers resign tomorrow?";

const retryDelay = (attempt: number) => new Promise((resolve) => window.setTimeout(resolve, 900 * (attempt + 1)));

export function MultiAgentWorkforcePanel() {
  const [analysis, setAnalysis] = useState<MultiAgentWorkforceResponse | null>(null);
  const [council, setCouncil] = useState<AgentCouncilResponse | null>(null);
  const [question, setQuestion] = useState("Why is company health declining?");
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUpdateUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = 0;
    try {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          const payload = await fetchJson<MultiAgentWorkforceResponse>("/api/agents/workforce/default");
          if (!isWorkforce(payload)) throw new Error("Malformed multi-agent payload");
          setAnalysis(payload);
          setStreamStatus((status) => (status === "connecting" ? "polling" : status));
          return;
        } catch (loadError) {
          if (attempt === 2) throw loadError;
          await retryDelay(attempt);
        }
      }
    } catch {
      setError("Multi-Agent AI Workforce could not load live orchestration.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askCouncil = useCallback(async () => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      const payload = await fetchJson<AgentCouncilResponse>("/api/agents/workforce/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, include_simulation: true }),
      });
      if (isCouncil(payload)) setCouncil(payload);
    } catch {
      setError("Executive AI Council request failed.");
    } finally {
      setAsking(false);
    }
  }, [question]);

  const runSimulation = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = Date.now() + 30000;
    setQuestion(BOARDROOM_DEMO_QUESTION);
    try {
      const payload = await fetchJson<MultiAgentWorkforceResponse>("/api/agents/workforce/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: BOARDROOM_DEMO_QUESTION,
          scenario_type: "workforce_change",
          resignation_count: 30,
          workload_delta_percent: 42,
        }),
      });
      if (!isWorkforce(payload)) throw new Error("Malformed simulation payload");
      setAnalysis(payload);
      setCouncil(null);
    } catch {
      setError("Agent workforce simulation failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/agents/workforce/stream");
    source.addEventListener("multi_agent_workforce", (event) => {
      if (Date.now() < manualUpdateUntil.current) return;
      try {
        const payload = JSON.parse((event as MessageEvent).data) as MultiAgentWorkforceResponse;
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

  const decision = analysis?.decisions[0];
  const simulation = analysis?.simulations[0];
  const boardroomStages = council?.boardroomStages ?? analysis?.boardroomStages ?? [];
  const consensus = council?.consensus ?? analysis?.consensus ?? null;
  const reasoningTraces = council?.reasoningTraces ?? analysis?.reasoningTraces ?? [];
  const debateExchanges = council?.debateExchanges ?? analysis?.debateExchanges ?? [];
  const consensusVotes = council?.consensusVotes ?? analysis?.consensusVotes ?? [];
  const researchMetrics = council?.researchMetrics ?? analysis?.researchMetrics ?? null;
  const activeSimulation = council?.simulation ?? simulation ?? null;
  const healthData = useMemo(
    () =>
      analysis?.analytics.map((item) => ({
        agent: item.agent.replace(" Agent", ""),
        health: Math.round(item.healthScore),
        workload: Math.round(item.workloadScore),
        latency: item.averageResponseMs,
      })) ?? [],
    [analysis],
  );
  const workflowData = useMemo(
    () =>
      analysis?.workflows.map((item) => ({
        name: item.name.split(" ").slice(0, 2).join(" "),
        reduction: Math.round(item.expectedRiskReduction),
      })) ?? [],
    [analysis],
  );

  return (
    <section
      id="multi-agent-workforce-panel"
      data-testid="multi-agent-workforce-panel"
      className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Bot className="size-4" />
            <span>Multi-Agent AI Workforce</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Autonomous AI manager agents coordinating company operations</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {analysis?.executiveBrief ?? "Verifying agent orchestration, shared memory, secure tools, workflows, and Executive AI Council decisions."}
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
            onClick={() => void runSimulation()}
            className="inline-flex h-10 items-center gap-2 border border-mint/35 bg-mint/10 px-3 text-sm text-mint transition hover:border-mint"
          >
            <Play className="size-4" />
            AI Boardroom Demo: 30 engineers resign
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-6">
        <Metric icon={Cpu} label="Active Agents" value={analysis ? String(analysis.summary.activeAgents) : "verifying"} />
        <Metric icon={MessageSquare} label="Messages" value={analysis ? String(analysis.summary.messages) : "verifying"} />
        <Metric icon={Workflow} label="Workflows" value={analysis ? String(analysis.summary.workflows) : "verifying"} />
        <Metric icon={Brain} label="Coordination" value={analysis ? `${Math.round(analysis.summary.coordinationScore)}%` : "verifying"} />
        <Metric icon={ShieldCheck} label="Readiness" value={analysis ? `${Math.round(analysis.summary.productionReadinessScore)}%` : "verifying"} />
        <Metric icon={Sparkles} label="Innovation" value={analysis ? `${Math.round(analysis.summary.innovationScore)}%` : "verifying"} />
      </div>

      <AIBoardroom
        stages={boardroomStages}
        consensus={consensus}
        simulation={activeSimulation}
        debateExchanges={debateExchanges}
        consensusVotes={consensusVotes}
        reasoningTraces={reasoningTraces}
        researchMetrics={researchMetrics}
      />

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <Panel title="AI Manager Agents" icon={Network}>
          <div className="grid gap-2 md:grid-cols-2">
            {analysis?.agents.map((agent) => (
              <div key={agent.agentId} className="border border-line/70 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{agent.role}</p>
                  </div>
                  <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-[10px] uppercase text-mint">{agent.status}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-1">
                  {agent.toolPermissions.slice(0, 3).map((tool) => (
                    <span key={tool} className="border border-line/60 bg-panel2/60 px-2 py-1 text-[10px] text-slate-400">
                      {tool}
                    </span>
                  ))}
                </div>
                <p className="mt-3 line-clamp-2 text-[11px] leading-5 text-slate-500">{agent.systemPrompt}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Executive AI Council" icon={Sparkles}>
          <div className="flex gap-2">
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              className="h-10 min-w-0 flex-1 border border-line bg-void px-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan/60"
              aria-label="Executive AI Council question"
            />
            <button
              type="button"
              onClick={() => void askCouncil()}
              className="inline-flex h-10 items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 text-sm text-cyan"
            >
              {asking ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              Ask
            </button>
          </div>
          <div className="mt-3 border border-line/70 bg-void/35 p-3">
            <div className="flex items-center justify-between gap-3 text-xs uppercase text-slate-500">
              <span>{council?.intent ?? "default council"}</span>
              <span>{council ? `${Math.round(council.confidence * 100)}% confidence` : "ready"}</span>
            </div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              {council?.answer ?? decision?.recommendation ?? "Executive Agent is waiting for a council question."}
            </p>
          </div>
          <div className="mt-3 grid gap-2">
            {(council?.councilTurns ?? analysis?.councilTurns ?? []).slice(0, 5).map((turn) => (
              <div key={`${turn.agent}-${turn.workflowTrigger}`} className="border border-line/60 bg-panel2/45 p-2">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold text-white">{turn.agent}</span>
                  <span className="text-[10px] text-cyan">{Math.round(turn.confidence)}%</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-500">{turn.recommendation}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-4">
        <Panel title="Communication Bus" icon={Cable}>
          <StatusLine label="Status" value={analysis?.communicationBus.status ?? "verifying"} />
          <StatusLine label="Messages" value={analysis ? String(analysis.communicationBus.messageCount) : "verifying"} />
          <StatusLine label="Latency" value={analysis ? `${analysis.communicationBus.averageLatencyMs} ms` : "verifying"} />
          <p className="mt-3 text-xs leading-5 text-slate-500">{analysis?.communicationBus.protocol ?? "Typed inter-agent event bus will appear once loaded."}</p>
        </Panel>

        <Panel title="Shared Memory" icon={Brain}>
          <StatusLine label="Status" value={analysis?.sharedMemoryStatus.status ?? "verifying"} />
          <StatusLine label="Records" value={analysis ? String(analysis.sharedMemoryStatus.records) : "verifying"} />
          <StatusLine label="Persistent" value={analysis?.sharedMemoryStatus.persistent ? "yes" : "verifying"} />
          <p className="mt-3 text-xs leading-5 text-slate-500">{analysis?.sharedMemoryStatus.retrievalStrategy ?? "Persistent memory strategy will appear once loaded."}</p>
        </Panel>

        <Panel title="Monitoring" icon={Radio}>
          <StatusLine label="Status" value={analysis?.monitoring.status ?? "verifying"} />
          <StatusLine label="Avg response" value={analysis ? `${analysis.monitoring.averageResponseMs} ms` : "verifying"} />
          <StatusLine label="Success" value={analysis ? `${Math.round(analysis.monitoring.averageSuccessRate)}%` : "verifying"} />
          <p className="mt-3 text-xs leading-5 text-slate-500">{analysis?.monitoring.monitoredMetrics.slice(0, 4).join(", ") ?? "Monitoring metrics will appear once loaded."}</p>
        </Panel>

        <Panel title="Security Controls" icon={ShieldCheck}>
          <div className="grid gap-2">
            {analysis?.securityControls.map((control) => (
              <div key={control.control} className="border border-line/60 bg-void/35 p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-semibold uppercase text-white">{control.control.replaceAll("_", " ")}</span>
                  <span className="text-[10px] uppercase text-mint">{control.status}</span>
                </div>
                <p className="mt-1 text-[11px] leading-4 text-slate-500">{control.evidence}</p>
              </div>
            )) ?? <p className="text-xs text-slate-500">Security controls will appear once loaded.</p>}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel title="Agent Health" icon={ShieldCheck}>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={healthData}>
                <CartesianGrid stroke="#1C2B3A" vertical={false} />
                <XAxis dataKey="agent" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="health" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                <Bar dataKey="workload" fill="#2DD4BF" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Collaboration Workflows" icon={GitBranch}>
          <div className="grid gap-3 md:grid-cols-[0.8fr_1.2fr]">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={workflowData}>
                  <CartesianGrid stroke="#1C2B3A" vertical={false} />
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 50]} />
                  <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                  <Line type="monotone" dataKey="reduction" stroke="#F6B44B" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="grid max-h-64 gap-2 overflow-y-auto pr-1">
              {analysis?.workflows.map((workflow) => (
                <WorkflowCard key={workflow.workflowId} workflow={workflow} />
              ))}
            </div>
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Shared Memory" icon={Cable}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {analysis?.memory.slice(0, 8).map((memory) => (
              <div key={memory.memoryId} className="border border-line/60 bg-void/35 p-2">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold text-white">{memory.agent}</span>
                  <span className="text-[10px] uppercase text-cyan">{memory.memoryType.replace("_", " ")}</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-500">{memory.value}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Autonomous Tasks" icon={CheckCircle2}>
          <div className="grid max-h-72 gap-2 overflow-y-auto pr-1">
            {analysis?.autonomousTasks.slice(0, 8).map((task) => (
              <div key={task.taskId} className="border border-line/60 bg-panel2/45 p-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-white">{task.owner}</span>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${riskTone[task.priority]}`}>{task.priority}</span>
                </div>
                <p className="mt-1 text-xs leading-5 text-slate-500">{task.task}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Digital Twin Simulation" icon={Radio}>
          <div className="border border-line/60 bg-void/35 p-3">
            <div className="text-xs uppercase text-cyan">{simulation?.scenarioType ?? "workforce_change"}</div>
            <p className="mt-2 text-sm leading-6 text-slate-300">
              {simulation?.question ?? "Simulation evidence will appear after the first agent cycle."}
            </p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <MiniMetric label="Delay" value={simulation ? `${Math.round(simulation.delayProbability)}%` : "verifying"} />
              <MiniMetric label="Revenue" value={simulation ? `${simulation.revenueImpactPercent.toFixed(1)}%` : "verifying"} />
              <MiniMetric label="Burnout" value={simulation ? `+${simulation.burnoutDelta.toFixed(1)}` : "verifying"} />
              <MiniMetric label="Confidence" value={simulation ? `${Math.round(simulation.confidence * 100)}%` : "verifying"} />
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              {simulation?.recommendedResponse[0] ?? "Executive Agent will synthesize scenario response once loaded."}
            </p>
          </div>
        </Panel>
      </div>

      {analysis?.finalVerdict ? <p className="mt-4 border border-cyan/30 bg-cyan/10 p-3 text-sm font-semibold text-cyan">{analysis.finalVerdict}</p> : null}
    </section>
  );
}

function AIBoardroom({
  stages,
  consensus,
  simulation,
  debateExchanges,
  consensusVotes,
  reasoningTraces,
  researchMetrics,
}: {
  stages: AgentBoardroomStage[];
  consensus: AgentCouncilConsensus | null;
  simulation: AgentSimulationResult | null;
  debateExchanges: AgentDebateExchange[];
  consensusVotes: AgentConsensusVote[];
  reasoningTraces: AgentReasoningTrace[];
  researchMetrics: AgentResearchMetrics | null;
}) {
  return (
    <article
      data-testid="ai-boardroom-council"
      className="mt-5 overflow-hidden border border-cyan/30 bg-[radial-gradient(circle_at_top_left,rgba(45,212,191,0.18),rgba(8,17,31,0.9)_42%,rgba(2,6,23,0.96))] shadow-control"
    >
      <div className="flex flex-col gap-3 border-b border-cyan/15 p-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.22em] text-cyan">AI Boardroom</p>
          <h3 className="mt-2 text-xl font-semibold text-white">Executive AI Council live decision meeting</h3>
          <p className="mt-1 text-sm leading-6 text-slate-400">
            Specialized AI managers read shared memory, digital twins, forecasts, and simulation evidence, then converge on one Executive Agent decision.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-2 text-center sm:grid-cols-4">
          <MiniMetric label="Delay" value={simulation ? `${Math.round(simulation.delayProbability)}%` : "verifying"} />
          <MiniMetric label="Revenue" value={simulation ? `${simulation.revenueImpactPercent.toFixed(1)}%` : "verifying"} />
          <MiniMetric label="Burnout" value={simulation ? `+${simulation.burnoutDelta.toFixed(1)}` : "verifying"} />
          <MiniMetric label="Consensus" value={consensus ? `${Math.round(consensus.confidence)}%` : "verifying"} />
          <MiniMetric label="Disputes" value={researchMetrics ? String(researchMetrics.disagreementCount) : "verifying"} />
          <MiniMetric label="Evidence" value={researchMetrics ? `${Math.round(researchMetrics.evidenceCoverageScore)}%` : "verifying"} />
          <MiniMetric label="Explain" value={researchMetrics ? `${Math.round(researchMetrics.explainabilityScore)}%` : "verifying"} />
          <MiniMetric label="Risk Vote" value={consensus ? `${Math.round(consensus.riskWeightedScore)}%` : "verifying"} />
        </div>
      </div>

      <div className="grid gap-4 p-4 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="grid gap-3 md:grid-cols-2">
          {stages.map((stage) => (
            <div
              key={`${stage.stage}-${stage.agent}`}
              className="relative min-h-44 overflow-hidden border border-line/70 bg-panel/70 p-3 transition duration-300 hover:border-cyan/45"
            >
              <div className="absolute right-3 top-3 size-2.5 animate-pulse rounded-full" style={{ backgroundColor: agentAccent[stage.agent], boxShadow: `0 0 16px ${agentAccent[stage.agent]}` }} />
              <div className="flex items-start gap-3">
                <div
                  className="grid size-11 place-items-center border text-sm font-semibold text-white"
                  style={{ borderColor: `${agentAccent[stage.agent]}80`, backgroundColor: `${agentAccent[stage.agent]}22` }}
                >
                  {stage.agent.split(" ")[0].slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h4 className="text-sm font-semibold text-white">{stage.agent}</h4>
                    <span className="border border-line/60 bg-void/45 px-2 py-0.5 text-[10px] uppercase text-slate-400">{stage.phase}</span>
                    <span className="border px-2 py-0.5 text-[10px] uppercase" style={{ borderColor: `${agentAccent[stage.agent]}66`, color: agentAccent[stage.agent] }}>
                      {stage.status}
                    </span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{stage.message}</p>
                </div>
              </div>
              <p className="mt-3 border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-300">{stage.recommendation}</p>
              <div className="mt-3 flex flex-wrap gap-1">
                {stage.evidence.slice(0, 4).map((item) => (
                  <span key={`${stage.agent}-${item}`} className="border border-cyan/15 bg-cyan/10 px-2 py-1 text-[10px] text-cyan">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="border border-line/70 bg-panel2/70 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-cyan">Final Executive Decision</p>
          <h4 className="mt-2 text-lg font-semibold text-white">{consensus?.ownerAgent ?? "Executive Agent"}</h4>
          <p className="mt-3 text-sm leading-6 text-slate-300">
            {consensus?.finalDecision ?? "Executive Agent is waiting for all AI managers to complete the boardroom discussion."}
          </p>

          <div className="mt-4 grid grid-cols-3 gap-2">
            <MiniMetric label="Majority" value={consensus?.majorityVote.replace("_", " ") ?? "verifying"} />
            <MiniMetric label="Agreement" value={consensus?.agreementLevel ?? "verifying"} />
            <MiniMetric label="Risk Score" value={consensus ? `${Math.round(consensus.riskWeightedScore)}%` : "verifying"} />
          </div>
          {consensus?.conflictResolutionSummary ? (
            <p className="mt-3 border border-cyan/20 bg-cyan/10 p-2 text-xs leading-5 text-cyan">{consensus.conflictResolutionSummary}</p>
          ) : null}

          <div className="mt-4">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Recommended Actions</p>
            <div className="mt-2 grid gap-2">
              {(consensus?.recommendedActions ?? []).slice(0, 5).map((action) => (
                <p key={action} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-300">
                  {action}
                </p>
              ))}
            </div>
          </div>

          <div className="mt-4">
            <p className="text-xs uppercase tracking-[0.16em] text-slate-500">Digital Twin + Simulation Evidence</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {[...(consensus?.digitalTwinEvidence ?? []), ...(consensus?.simulationEvidence ?? [])].slice(0, 8).map((item) => (
                <span key={item} className="border border-mint/20 bg-mint/10 px-2 py-1 text-[11px] text-mint">
                  {item}
                </span>
              ))}
            </div>
          </div>

          {consensus?.dissentingRisks.length ? (
            <div className="mt-4">
              <p className="text-xs uppercase tracking-[0.16em] text-amber">Escalated Risks</p>
              <div className="mt-2 grid gap-2">
                {consensus.dissentingRisks.map((risk) => (
                  <p key={risk} className="border border-amber/25 bg-amber/10 p-2 text-xs leading-5 text-amber">
                    {risk}
                  </p>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 border-t border-cyan/15 p-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div>
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs uppercase tracking-[0.18em] text-cyan">Agent Debate + Disagreements</p>
            <span className="border border-cyan/20 bg-cyan/10 px-2 py-1 text-[10px] uppercase text-cyan">
              {debateExchanges.length} negotiation rounds
            </span>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {debateExchanges.map((exchange) => (
              <div key={exchange.exchangeId} className="border border-line/70 bg-panel/70 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-white">{exchange.fromAgent}</span>
                  <span className="text-[10px] uppercase text-slate-500">challenged</span>
                  <span className="text-xs font-semibold text-white">{exchange.toAgent}</span>
                  <span className="border border-amber/25 bg-amber/10 px-2 py-0.5 text-[10px] uppercase text-amber">{exchange.resolution}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{exchange.disagreement}</p>
                <p className="mt-2 border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-300">{exchange.challenge}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">{exchange.response}</p>
                <div className="mt-3 flex flex-wrap gap-1">
                  {exchange.evidence.slice(0, 4).map((item) => (
                    <span key={`${exchange.exchangeId}-${item}`} className="border border-cyan/15 bg-cyan/10 px-2 py-1 text-[10px] text-cyan">
                      {item}
                    </span>
                  ))}
                </div>
                <div className="mt-2 h-1.5 overflow-hidden bg-void">
                  <div className="h-full bg-amber" style={{ width: `${Math.round(exchange.disagreementScore)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="grid gap-4">
          <div className="border border-line/70 bg-panel2/60 p-3">
            <p className="text-xs uppercase tracking-[0.18em] text-cyan">Consensus Votes</p>
            <div className="mt-3 grid gap-2">
              {consensusVotes.map((vote) => (
                <div key={vote.agent} className="border border-line/60 bg-void/35 p-2">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold text-white">{vote.agent}</span>
                    <span className={`border px-2 py-1 text-[10px] uppercase ${voteTone[vote.vote]}`}>{vote.vote.replace("_", " ")}</span>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-slate-500">{vote.rationale}</p>
                  <div className="mt-2 grid grid-cols-2 gap-2">
                    <MiniMetric label="Risk Weight" value={`${Math.round(vote.riskWeight)}%`} />
                    <MiniMetric label="Confidence" value={`${Math.round(vote.confidence)}%`} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-line/70 bg-panel2/60 p-3">
            <p className="text-xs uppercase tracking-[0.18em] text-cyan">Research Metrics</p>
            <div className="mt-3 grid grid-cols-2 gap-2">
              <MiniMetric label="Perspective" value={researchMetrics ? `${Math.round(researchMetrics.perspectiveDiversityScore)}%` : "verifying"} />
              <MiniMetric label="Consensus" value={researchMetrics ? `${Math.round(researchMetrics.consensusScore)}%` : "verifying"} />
              <MiniMetric label="Status" value={researchMetrics?.conflictResolutionStatus.replace("_", " ") ?? "verifying"} />
              <MiniMetric label="Rounds" value={researchMetrics ? String(researchMetrics.negotiationRounds) : "verifying"} />
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-500">
              {researchMetrics?.reasoningAbstractionLayer ??
                "Evidence-only reasoning trace will appear once agents complete negotiation."}
            </p>
          </div>
        </div>
      </div>

      <div className="border-t border-cyan/15 p-4">
        <p className="text-xs uppercase tracking-[0.18em] text-cyan">Reasoning Abstraction</p>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {reasoningTraces.slice(0, 6).map((trace) => (
            <div key={trace.agent} className="border border-line/70 bg-panel/65 p-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-semibold text-white">{trace.agent}</span>
                <span className="border border-line/60 bg-void/45 px-2 py-1 text-[10px] uppercase text-slate-400">{trace.uncertainty}</span>
              </div>
              <p className="mt-2 text-xs font-semibold text-cyan">{trace.perspective}</p>
              <p className="mt-2 text-xs leading-5 text-slate-400">{trace.reasoningSummary}</p>
              <p className="mt-2 border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-300">{trace.conclusion}</p>
              <div className="mt-3 flex flex-wrap gap-1">
                {trace.evidenceUsed.slice(0, 4).map((item) => (
                  <span key={`${trace.agent}-${item}`} className="border border-mint/15 bg-mint/10 px-2 py-1 text-[10px] text-mint">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </article>
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

function StatusLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-line/50 py-1.5 text-xs">
      <span className="uppercase text-slate-500">{label}</span>
      <span className="text-right font-semibold text-white">{value}</span>
    </div>
  );
}

function WorkflowCard({ workflow }: { workflow: AgentWorkflow }) {
  return (
    <div className="border border-line/60 bg-void/35 p-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-xs font-semibold text-white">{workflow.name}</h3>
          <p className="mt-1 text-[11px] leading-4 text-slate-500">{workflow.trigger}</p>
        </div>
        <span className="text-[10px] uppercase text-mint">{workflow.status}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1">
        {workflow.participants.map((agent) => (
          <span key={agent} className="border border-line/60 bg-panel2/60 px-2 py-1 text-[10px] text-slate-400">
            {agent.replace(" Agent", "")}
          </span>
        ))}
      </div>
    </div>
  );
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, cache: "no-store" });
  if (!response.ok) throw new Error(`Request failed: ${url}`);
  return (await response.json()) as T;
}

function isWorkforce(value: unknown): value is MultiAgentWorkforceResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "summary" in value &&
      Array.isArray((value as MultiAgentWorkforceResponse).agents) &&
      Array.isArray((value as MultiAgentWorkforceResponse).messages) &&
      Array.isArray((value as MultiAgentWorkforceResponse).boardroomStages) &&
      Array.isArray((value as MultiAgentWorkforceResponse).reasoningTraces) &&
      Array.isArray((value as MultiAgentWorkforceResponse).debateExchanges) &&
      Array.isArray((value as MultiAgentWorkforceResponse).consensusVotes) &&
      Boolean((value as MultiAgentWorkforceResponse).consensus) &&
      Boolean((value as MultiAgentWorkforceResponse).researchMetrics) &&
      Boolean((value as MultiAgentWorkforceResponse).communicationBus) &&
      Boolean((value as MultiAgentWorkforceResponse).sharedMemoryStatus) &&
      Boolean((value as MultiAgentWorkforceResponse).monitoring) &&
      Array.isArray((value as MultiAgentWorkforceResponse).securityControls),
  );
}

function isCouncil(value: unknown): value is AgentCouncilResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "answer" in value &&
      Array.isArray((value as AgentCouncilResponse).participatingAgents) &&
      Array.isArray((value as AgentCouncilResponse).boardroomStages) &&
      Array.isArray((value as AgentCouncilResponse).reasoningTraces) &&
      Array.isArray((value as AgentCouncilResponse).debateExchanges) &&
      Array.isArray((value as AgentCouncilResponse).consensusVotes) &&
      Boolean((value as AgentCouncilResponse).consensus),
  );
}
