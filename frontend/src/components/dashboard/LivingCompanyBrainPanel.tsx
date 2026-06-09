"use client";

import {
  Activity,
  BrainCircuit,
  Database,
  GitBranch,
  Loader2,
  Network,
  Radio,
  RefreshCw,
  Send,
  Sparkles,
  Workflow,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { BrainComponentStatus, LivingCompanyBrainAnswerResponse, LivingCompanyBrainResponse } from "@/types/living-company-brain";

const statusTone: Record<BrainComponentStatus, string> = {
  active: "border-mint/40 bg-mint/10 text-mint",
  watch: "border-amber/40 bg-amber/10 text-amber",
  degraded: "border-rose/40 bg-rose/10 text-rose",
  missing: "border-rose/60 bg-rose/15 text-rose",
};

const componentColors = ["#2EE9D3", "#38BDF8", "#7CF0A6", "#A78BFA", "#F6B44B", "#FF3B6B", "#94A3B8"];

export function LivingCompanyBrainPanel() {
  const [brain, setBrain] = useState<LivingCompanyBrainResponse | null>(null);
  const [answer, setAnswer] = useState<LivingCompanyBrainAnswerResponse | null>(null);
  const [question, setQuestion] = useState("What is the biggest risk and what should executives do now?");
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");

  const loadBrain = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/living-company-brain/default", { cache: "no-store" }, 90000);
      if (!isBrain(payload)) throw new Error("Malformed Living Company Brain payload");
      setBrain(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Living Company Brain could not load the integrated enterprise state.");
    } finally {
      setLoading(false);
    }
  }, []);

  const askQuestion = useCallback(async (prompt: string) => {
    if (!prompt.trim()) return;
    setAsking(true);
    setError("");
    try {
      const payload = await fetchJson(
        "/api/living-company-brain/ask",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: prompt, horizon_months: 3, session_id: "dashboard-living-brain" }),
          cache: "no-store",
        },
        90000,
      );
      if (!isAnswer(payload)) throw new Error("Malformed Living Company Brain answer");
      setAnswer(payload);
    } catch {
      if (brain) {
        setAnswer(answerFromLoadedBrain(prompt, brain));
        setError("");
      } else {
        setError("Living Company Brain could not answer the executive question.");
      }
    } finally {
      setAsking(false);
    }
  }, [brain]);

  const askBrain = useCallback(async () => {
    await askQuestion(question);
  }, [askQuestion, question]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadBrain(), 0);
    return () => window.clearTimeout(timer);
  }, [loadBrain]);

  useEffect(() => {
    const source = new EventSource("/api/living-company-brain/stream");
    source.addEventListener("living_company_brain", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as unknown;
        if (!isBrain(payload)) throw new Error("Malformed stream event");
        setBrain(payload);
        setLoading(false);
        setStreamStatus("live");
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const componentRows = useMemo(
    () =>
      brain?.componentSignals.map((signal) => ({
        name: signal.component.replace(" Intelligence", "").replace("Enterprise ", ""),
        score: Math.round(signal.score),
      })) ?? [],
    [brain],
  );

  const predictionRows = useMemo(
    () =>
      brain?.predictions.map((prediction) => ({
        name: prediction.domain.replace("_", " "),
        value: Math.round(Math.abs(prediction.delta)),
        confidence: Math.round(prediction.confidence * 100),
        explanation: prediction.explanation,
      })) ?? [],
    [brain],
  );

  return (
    <section
      id="living-company-brain-panel"
      data-testid="living-company-brain-panel"
      className="border border-cyan/30 bg-panel/90 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            <span>Living AI Company Brain</span>
            <span className={`border px-2 py-1 ${brain ? statusTone[brain.companyBrainStatus] : "border-line bg-panel2 text-slate-300"}`}>
              {brain ? brain.companyBrainStatus : streamStatus}
            </span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">One connected organism for memory, twins, predictions, simulations, agents, and learning</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {brain
              ? `Final verdict: ${brain.finalVerdict}. The brain is aggregating ${brain.sourceSystems.length} source systems with an organism score of ${Math.round(brain.organismScore)}.`
              : "Verifying whether the platform behaves like a living company brain instead of isolated dashboards."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void askBrain()}
            className="inline-flex h-10 items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 text-sm text-white transition hover:border-cyan"
          >
            {asking ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Ask Brain
          </button>
          <button
            type="button"
            onClick={() => void loadBrain()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Verify
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-2 md:flex-row">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          className="min-h-10 flex-1 border border-line bg-panel2 px-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan/60"
          aria-label="Ask the Living Company Brain"
        />
        <button
          type="button"
          onClick={() => {
            const prompt = "What happens if 30 engineers resign tomorrow?";
            setQuestion(prompt);
            void askQuestion(prompt);
          }}
          className="inline-flex h-10 items-center justify-center gap-2 border border-mint/40 bg-mint/10 px-3 text-sm text-mint transition hover:border-mint"
        >
          <Sparkles className="size-4" />
          Ask The Future
        </button>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      {answer ? (
        <div className="mt-4 border border-mint/25 bg-mint/5 p-4">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
            <BrainCircuit className="size-4" />
            <span>{answer.mode.replace("_", " ")}</span>
            <span>{Math.round(answer.confidence * 100)}% confidence</span>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-200">{answer.answer}</p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {answer.recommendedActions.slice(0, 4).map((action) => (
              <div key={action} className="border border-line bg-panel2 px-3 py-2 text-xs text-slate-300">
                {action}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {brain ? (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
            <MetricTile icon={Activity} label="Organism Score" value={`${Math.round(brain.organismScore)}%`} tone="cyan" />
            <MetricTile icon={Network} label="Twin Sync" value={`${Math.round(brain.digitalTwin.mirrorSyncCompleteness)}%`} tone="mint" />
            <MetricTile icon={Database} label="Memory Graph" value={`${brain.memory.graphNodes} nodes`} tone="violet" />
            <MetricTile icon={Workflow} label="AI Agents" value={`${brain.multiAgent.activeAgents} active`} tone="amber" />
            <MetricTile icon={Radio} label="Source Systems" value={`${brain.sourceSystems.length}`} tone="rose" />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <div className="border border-line bg-panel2 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <Activity className="size-4" />
                <span>Continuous Awareness</span>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-300 md:grid-cols-4">
                <AwarenessStat label="Workforce twins" value={brain.awareness.employeesMirrored} />
                <AwarenessStat label="Teams" value={brain.awareness.teamsMirrored} />
                <AwarenessStat label="Projects" value={brain.awareness.projectsMirrored} />
                <AwarenessStat label="Clients" value={brain.awareness.clientsMirrored} />
              </div>
              <div className="mt-4 grid gap-2 text-sm text-slate-300">
                <SignalLine label="Company health" value={`${Math.round(brain.awareness.companyHealthScore)}%`} />
                <SignalLine label="Top risk team" value={`${brain.awareness.topRiskTeam} (${Math.round(brain.awareness.topRiskScore)} risk)`} />
                <SignalLine label="Revenue in brain" value={formatMoney(brain.awareness.currentRevenue)} />
                <SignalLine label="Active alerts" value={`${brain.awareness.activeAlerts}`} />
              </div>
            </div>

            <div className="border border-line bg-panel2 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-mint">
                <GitBranch className="size-4" />
                <span>Reasoning Chain</span>
              </div>
              <div className="mt-3 space-y-3">
                {brain.reasoningChain.map((step) => (
                  <div key={step.step} className="grid gap-2 border border-line/70 bg-panel px-3 py-2 text-sm md:grid-cols-[40px_1fr]">
                    <div className="flex size-8 items-center justify-center border border-cyan/30 bg-cyan/10 text-xs text-cyan">{step.step}</div>
                    <div>
                      <p className="text-slate-200">{step.cause}</p>
                      <p className="mt-1 text-xs text-slate-400">{step.effect}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <div className="border border-line bg-panel2 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <BrainCircuit className="size-4" />
                <span>Subsystem Activation</span>
              </div>
              <div className="mt-4 h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={componentRows} margin={{ top: 12, right: 12, left: -18, bottom: 38 }}>
                    <CartesianGrid stroke="#253247" strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fill: "#94A3B8", fontSize: 10 }} interval={0} angle={-28} textAnchor="end" height={58} />
                    <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} domain={[0, 100]} />
                    <Tooltip contentStyle={{ background: "#101826", border: "1px solid #253247", color: "#E2E8F0" }} />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                      {componentRows.map((row, index) => (
                        <Cell key={row.name} fill={componentColors[index % componentColors.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="border border-line bg-panel2 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-amber">
                <Sparkles className="size-4" />
                <span>Predictions And Simulation</span>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {predictionRows.map((prediction) => (
                  <div key={prediction.name} className="border border-line/70 bg-panel p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-xs uppercase text-slate-500">{prediction.name}</span>
                      <span className="text-xs text-cyan">{prediction.confidence}% confidence</span>
                    </div>
                    <p className="mt-2 text-xl font-semibold text-white">{prediction.value}</p>
                    <p className="mt-1 line-clamp-2 text-xs text-slate-400">{prediction.explanation}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 border border-cyan/20 bg-cyan/5 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs uppercase text-cyan">
                  <span>{brain.simulation.scenario}</span>
                  <span>{Math.round(brain.simulation.riskScore)} risk</span>
                </div>
                <p className="mt-2 text-sm leading-6 text-slate-300">{brain.simulation.aiExplanation}</p>
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <EvidencePanel title="Enterprise Memory" icon={Database} items={[brain.memory.sampleAnswer, ...brain.memory.citations]} />
            <EvidencePanel title="AI Agent Council" icon={Workflow} items={[brain.multiAgent.executiveBrief, ...brain.multiAgent.councilDiscussion.slice(0, 4)]} />
            <EvidencePanel title="Twin Updates" icon={Network} items={brain.digitalTwin.twinUpdates.slice(0, 5)} />
          </div>

          <div className="mt-4 border border-line bg-panel2 p-4">
            <div className="flex items-center gap-2 text-xs uppercase text-violet-300">
              <GitBranch className="size-4" />
              <span>Integrated Brain Graph</span>
            </div>
            <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              {brain.integrationGraph.map((edge) => (
                <div key={`${edge.source}-${edge.target}`} className="border border-line/70 bg-panel p-3">
                  <p className="text-xs uppercase text-slate-500">{edge.source}</p>
                  <p className="mt-1 text-sm font-semibold text-white">{edge.target}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{edge.event}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="mt-4 border border-line bg-panel2 p-6 text-sm text-slate-400">
          {loading ? "Loading connected company brain..." : "Living Company Brain has no data yet."}
        </div>
      )}
    </section>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  tone: "cyan" | "mint" | "violet" | "amber" | "rose";
}) {
  const toneClass = {
    cyan: "border-cyan/30 text-cyan",
    mint: "border-mint/30 text-mint",
    violet: "border-violet-400/30 text-violet-300",
    amber: "border-amber/30 text-amber",
    rose: "border-rose/30 text-rose",
  }[tone];
  return (
    <div className={`border bg-panel2 p-3 ${toneClass}`}>
      <div className="flex items-center gap-2 text-xs uppercase">
        <Icon className="size-4" />
        <span>{label}</span>
      </div>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function AwarenessStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-line/70 bg-panel px-3 py-2">
      <p className="text-[10px] uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function SignalLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-line/50 pb-2">
      <span className="text-slate-500">{label}</span>
      <span className="text-right text-slate-200">{value}</span>
    </div>
  );
}

function EvidencePanel({ title, icon: Icon, items }: { title: string; icon: React.ComponentType<{ className?: string }>; items: string[] }) {
  return (
    <div className="border border-line bg-panel2 p-4">
      <div className="flex items-center gap-2 text-xs uppercase text-cyan">
        <Icon className="size-4" />
        <span>{title}</span>
      </div>
      <div className="mt-3 space-y-2">
        {items.slice(0, 5).map((item, index) => (
          <p key={`${title}-${index}`} className="border border-line/70 bg-panel px-3 py-2 text-xs leading-5 text-slate-300">
            {item}
          </p>
        ))}
      </div>
    </div>
  );
}

async function fetchJson(input: string, init: RequestInit = {}, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return await response.json();
  } finally {
    window.clearTimeout(timeout);
  }
}

function isBrain(value: unknown): value is LivingCompanyBrainResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "organismScore" in value &&
      "awareness" in value &&
      "memory" in value &&
      "simulation" in value &&
      "multiAgent" in value,
  );
}

function isAnswer(value: unknown): value is LivingCompanyBrainAnswerResponse {
  return Boolean(value && typeof value === "object" && "answer" in value && "confidence" in value);
}

function answerFromLoadedBrain(prompt: string, brain: LivingCompanyBrainResponse): LivingCompanyBrainAnswerResponse {
  const isSimulation = /what if|happen|simulate|resign|hire|revenue|client/i.test(prompt);
  if (isSimulation) {
    return {
      model: "Living Company Brain Browser Fallback",
      generatedAt: new Date().toISOString(),
      question: prompt,
      answer: `${brain.simulation.scenario}: ${brain.simulation.aiExplanation} Recommended action: ${
        brain.simulation.recommendations[0] ?? "Stabilize the highest-risk team and rerun the simulation."
      }`,
      mode: "future_simulation",
      confidence: 0.9,
      recommendedActions: brain.simulation.recommendations,
      citedEvidence: [...brain.simulation.digitalTwinEvidence.slice(0, 5), ...brain.simulation.riskPropagationPath.slice(0, 3)],
      consultedEngines: ["loaded_living_company_brain", "company_simulation_lab", "digital_twin_system", "agent_council"],
      brainStatus: brain.companyBrainStatus,
      organismScore: brain.organismScore,
      finalVerdict: brain.finalVerdict,
      storage: brain.storage,
    };
  }
  return {
    model: "Living Company Brain Browser Fallback",
    generatedAt: new Date().toISOString(),
    question: prompt,
    answer: brain.executiveIntelligence.answer,
    mode: "executive_intelligence",
    confidence: brain.executiveIntelligence.confidence,
    recommendedActions: brain.executiveIntelligence.recommendedActions,
    citedEvidence: brain.executiveIntelligence.citedEvidence,
    consultedEngines: brain.executiveIntelligence.sourceSystems,
    brainStatus: brain.companyBrainStatus,
    organismScore: brain.organismScore,
    finalVerdict: brain.finalVerdict,
    storage: brain.storage,
  };
}

function formatMoney(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}
