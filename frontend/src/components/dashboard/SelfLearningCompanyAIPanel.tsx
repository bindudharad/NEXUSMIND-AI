"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { Activity, BrainCircuit, CheckCircle2, Database, GitBranch, Loader2, RefreshCw, Send, Sparkles, Workflow } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { LearningStatus, SelfLearningAIResponse, SelfLearningAssistantResponse } from "@/types/self-learning-ai";

type SnakeRecord = Record<string, unknown>;

const statusTone: Record<LearningStatus, string> = {
  ready: "border-mint/40 bg-mint/10 text-mint",
  learning: "border-cyan/40 bg-cyan/10 text-cyan",
  degraded: "border-amber/40 bg-amber/10 text-amber",
  missing: "border-rose/40 bg-rose/10 text-rose",
};

const scoreColors = ["#2EE9D3", "#38BDF8", "#7CF0A6", "#A78BFA", "#F6B44B", "#FF3B6B", "#94A3B8", "#F472B6"];

export function SelfLearningCompanyAIPanel() {
  const [audit, setAudit] = useState<SelfLearningAIResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [feedbackState, setFeedbackState] = useState<"idle" | "sending" | "sent">("idle");
  const [assistant, setAssistant] = useState<SelfLearningAssistantResponse | null>(null);
  const [assistantState, setAssistantState] = useState<"idle" | "asking">("idle");
  const [demoState, setDemoState] = useState<"idle" | "running">("idle");
  const [error, setError] = useState("");
  const manualDemoUntil = useRef(0);

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/self-learning/verification", { cache: "no-store" });
      if (!response.ok) throw new Error("Self-learning verification failed");
      setAudit((await response.json()) as SelfLearningAIResponse);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Self-learning company AI verification could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadAudit(), 0);
    return () => window.clearTimeout(timer);
  }, [loadAudit]);

  useEffect(() => {
    const source = new EventSource("/api/self-learning/stream");
    source.addEventListener("self_learning_company_ai", (event) => {
      if (Date.now() < manualDemoUntil.current) return;
      try {
        setAudit(toCamel<SelfLearningAIResponse>(JSON.parse((event as MessageEvent).data)));
        setLoading(false);
        setStreamStatus("live");
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const sendFeedback = useCallback(async () => {
    setFeedbackState("sending");
    try {
      await fetch("/api/self-learning/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_system: "self_learning_dashboard",
          signal_type: "recommendation",
          accepted: true,
          usefulness_score: 5,
          outcome: "Executive dashboard learning signal validated.",
        }),
      });
      setFeedbackState("sent");
      await loadAudit();
    } catch {
      setFeedbackState("idle");
      setError("Self-learning feedback could not be stored.");
    }
  }, [loadAudit]);

  const askAssistant = useCallback(async () => {
    setAssistantState("asking");
    setError("");
    try {
      const response = await fetch("/api/self-learning/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: "Which models need retraining and why?" }),
      });
      if (!response.ok) throw new Error("Self-learning assistant failed");
      setAssistant((await response.json()) as SelfLearningAssistantResponse);
    } catch {
      setError("Self-learning assistant could not answer.");
    } finally {
      setAssistantState("idle");
    }
  }, []);

  const runDemo = useCallback(async () => {
    setDemoState("running");
    setError("");
    manualDemoUntil.current = Date.now() + 45000;
    try {
      const response = await fetch("/api/self-learning/demo", {
        method: "POST",
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Self-learning demo failed");
      const payload = (await response.json()) as SelfLearningAIResponse;
      setAudit(payload);
      setStreamStatus("demo");
    } catch {
      setError("Self-learning demo could not run.");
    } finally {
      setDemoState("idle");
    }
  }, []);

  const scoreRows = useMemo(() => {
    if (!audit) return [];
    return [
      { name: "Learning", score: audit.scorecard.learningEngineScore },
      { name: "Adaptive", score: audit.scorecard.adaptiveRecommendationScore },
      { name: "Feedback", score: audit.scorecard.feedbackLoopScore },
      { name: "Knowledge", score: audit.scorecard.knowledgeEvolutionScore },
      { name: "Agents", score: audit.scorecard.agentLearningScore },
      { name: "Twin", score: audit.scorecard.digitalTwinLearningScore },
      { name: "Predictions", score: audit.scorecard.predictionImprovementScore },
      { name: "Production", score: audit.scorecard.productionReadinessScore },
    ];
  }, [audit]);

  const patterns = useMemo(() => {
    if (!audit) return [];
    return [...audit.cultureInsights, ...audit.employeeBehaviorInsights, ...audit.businessPatternInsights].slice(0, 6);
  }, [audit]);

  return (
    <section
      id="self-learning-company-ai-panel"
      data-testid="self-learning-company-ai-panel"
      className="border border-mint/30 bg-panel/90 p-5 shadow-control backdrop-blur"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
            <BrainCircuit className="size-4" />
            <span>Self-Learning Company AI</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-mint">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Adaptive enterprise intelligence that learns from outcomes</h2>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            {audit
              ? `Final verdict: ${audit.finalVerdict}. The platform learns from feedback, operational histories, knowledge graph growth, multi-agent memory, model validation, and digital twin simulations.`
              : "Verifying continuous feedback loops, adaptive recommendations, knowledge evolution, agent learning, digital twin adaptation, and prediction improvement tracking."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => void sendFeedback()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-mint/60"
          >
            {feedbackState === "sending" ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            {feedbackState === "sent" ? "Learning Captured" : "Send Signal"}
          </button>
          <button
            type="button"
            onClick={() => void runDemo()}
            className="inline-flex h-10 items-center gap-2 border border-mint/45 bg-mint/10 px-3 text-sm text-mint transition hover:border-mint"
          >
            {demoState === "running" ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Self-Learning Demo
          </button>
          <button
            type="button"
            onClick={() => void askAssistant()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-mint/60"
          >
            {assistantState === "asking" ? <Loader2 className="size-4 animate-spin" /> : <BrainCircuit className="size-4" />}
            Ask Learning AI
          </button>
          <button
            type="button"
            onClick={() => void loadAudit()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel2 px-3 text-sm text-white transition hover:border-cyan/60"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Verify
          </button>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      {audit?.demoState ? <SelfLearningDemoPanel audit={audit} /> : null}

      {assistant ? (
        <div className="mt-4 border border-cyan/25 bg-cyan/5 p-4">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            <span>Learning AI Assistant</span>
            <span>{Math.round(assistant.confidence * 100)}% confidence</span>
          </div>
          <p className="mt-3 text-sm leading-6 text-white">{assistant.answer}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {assistant.actions.slice(0, 3).map((action) => (
              <span key={action} className="border border-line bg-void/35 px-2 py-1 text-xs text-slate-300">{action}</span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 grid gap-3 md:grid-cols-5">
        <Metric icon={CheckCircle2} label="Learning Status" value={audit?.learningEngineStatus ?? "verifying"} />
        <Metric icon={Sparkles} label="Recommendation Accuracy" value={audit ? `${Math.round(audit.recommendationAccuracy)}%` : "verifying"} />
        <Metric icon={Activity} label="Forecast Accuracy" value={audit ? `${Math.round(audit.forecastAccuracy)}%` : "verifying"} />
        <Metric icon={Workflow} label="Retraining Events" value={audit ? `${audit.retrainingEvents.length}` : "verifying"} />
        <Metric icon={Database} label="Learning Maturity" value={audit ? `${Math.round(audit.learningMaturityScore || audit.productionReadinessScore)}/100` : "verifying"} />
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel title="Adaptive Scorecard" icon={Activity}>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={scoreRows} layout="vertical" margin={{ left: 16, right: 12, top: 4, bottom: 4 }}>
                <CartesianGrid stroke="#1C2B3A" strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 100]} stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="name" width={92} stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ background: "#08111f", border: "1px solid #223044", color: "#e2e8f0" }} />
                <Bar dataKey="score" radius={[0, 3, 3, 0]}>
                  {scoreRows.map((entry, index) => (
                    <Cell key={entry.name} fill={scoreColors[index % scoreColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Learning Components" icon={Workflow}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1 md:grid-cols-2">
            {audit?.components.map((component) => (
              <div key={component.component} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{component.component}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[component.status]}`}>{component.status}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{Math.round(component.score)} score, {component.learningSignalCount} signals</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{component.evidence.slice(0, 2).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Learned Patterns" icon={BrainCircuit}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {patterns.map((item) => (
              <div key={`${item.domain}-${item.pattern}`} className="border border-line/60 bg-panel2/45 p-3">
                <div className="text-[10px] uppercase text-cyan">{item.domain.replace("_", " ")}</div>
                <h3 className="mt-1 text-sm font-semibold text-white">{Math.round(item.confidence)}% confidence</h3>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.pattern}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">{item.adaptation}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Feedback Loops and Outcomes" icon={GitBranch}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.feedbackLoops.map((loop) => (
              <div key={loop.loop} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{loop.loop}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[loop.status]}`}>{loop.status}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{loop.records} records, signal {loop.averageLearningSignal.toFixed(2)}, delta {loop.confidenceDelta.toFixed(1)}</p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{loop.adaptation}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Prediction Improvement" icon={Activity}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.predictionImprovements.map((metric) => (
              <div key={metric.metric} className="border border-line/60 bg-panel2/45 p-3">
                <h3 className="text-sm font-semibold text-white">{metric.metric}</h3>
                <div className="mt-2 flex items-end justify-between gap-3">
                  <span className="text-xs text-slate-500">Baseline {Math.round(metric.baselineAccuracy)}%</span>
                  <strong className="text-lg text-mint">{Math.round(metric.currentAccuracy)}%</strong>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">Improvement {metric.improvementPercent.toFixed(1)}% from {metric.evidence.slice(0, 2).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Model Evaluation" icon={Activity}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.modelEvaluations.map((metric) => (
              <div key={`${metric.modelName}-${metric.version}`} className="border border-line/60 bg-void/35 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{metric.modelName}</h3>
                  <span className={`border px-2 py-1 text-[10px] uppercase ${statusTone[metric.status]}`}>{metric.version}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Accuracy {Math.round(metric.accuracy)}%, F1 {Math.round(metric.f1Score)}%, MAE {metric.mae.toFixed(1)}, RMSE {metric.rmse.toFixed(1)}
                </p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{metric.evidence.slice(0, 2).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Drift Detection" icon={GitBranch}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.driftSignals.map((signal) => (
              <div key={`${signal.driftType}-${signal.domain}`} className="border border-line/60 bg-panel2/45 p-3">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-sm font-semibold text-white">{signal.driftType.replace("_", " ")}</h3>
                  <span className="border border-cyan/30 bg-cyan/10 px-2 py-1 text-[10px] uppercase text-cyan">{signal.status}</span>
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  {signal.domain}: {Math.round(signal.driftScore)} score / {Math.round(signal.threshold)} threshold
                </p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{signal.evidence.slice(0, 2).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Auto-Retraining" icon={RefreshCw}>
          <div className="grid max-h-80 gap-2 overflow-y-auto pr-1">
            {audit?.retrainingEvents.map((event) => (
              <div key={event.eventId} className="border border-line/60 bg-void/35 p-3">
                <h3 className="text-sm font-semibold text-white">{event.modelName}</h3>
                <p className="mt-2 text-xs text-slate-500">
                  {`${event.previousVersion} -> ${event.newVersion}, +${event.accuracyDelta.toFixed(1)} accuracy, ${event.trainingRecords} records`}
                </p>
                <p className="mt-2 text-xs leading-5 text-slate-400">{event.trigger.replace("_", " ")} | {event.evidence.slice(0, 2).join(" | ")}</p>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Knowledge Evolution" icon={Database}>
          <div className="grid grid-cols-2 gap-2">
            <MiniMetric label="Documents" value={audit?.knowledgeEvolution.documentsIndexed} />
            <MiniMetric label="Chunks" value={audit?.knowledgeEvolution.chunksIndexed} />
            <MiniMetric label="Graph Nodes" value={audit?.knowledgeEvolution.graphNodes} />
            <MiniMetric label="Solutions" value={audit?.knowledgeEvolution.solutionsDetected} />
          </div>
          <div className="mt-3 grid gap-2">
            {audit?.knowledgeEvolution.newBestPractices.slice(0, 3).map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
            ))}
          </div>
        </Panel>

        <Panel title="Agent Learning" icon={Workflow}>
          <div className="grid grid-cols-3 gap-2">
            <MiniMetric label="Agents" value={audit?.agentLearning.agents.length} />
            <MiniMetric label="Memory" value={audit?.agentLearning.sharedMemoryRecords} />
            <MiniMetric label="Messages" value={audit?.agentLearning.messages} />
          </div>
          <div className="mt-3 grid gap-2">
            {audit?.agentLearning.propagatedInsights.slice(0, 3).map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
            ))}
          </div>
        </Panel>

        <Panel title="Digital Twin Learning" icon={Sparkles}>
          <div className="grid grid-cols-2 gap-2">
            <MiniMetric label="Scenario" value={audit?.digitalTwinLearning.scenarioAccuracy} suffix="%" />
            <MiniMetric label="Simulation" value={audit?.digitalTwinLearning.simulationAccuracy} suffix="%" />
            <MiniMetric label="Forecast MAE" value={audit?.forecastLearning?.meanAbsoluteError} />
            <MiniMetric label="Calibration" value={audit?.simulationLearning?.scenariosCalibrated} />
          </div>
          <div className="mt-3 grid gap-2">
            {[...(audit?.digitalTwinLearning.adaptationSignals ?? []), ...(audit?.simulationLearning?.learnedAdjustments ?? [])].slice(0, 4).map((item) => (
              <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
            ))}
          </div>
        </Panel>
      </div>
    </section>
  );
}

function SelfLearningDemoPanel({ audit }: { audit: SelfLearningAIResponse }) {
  const demo = audit.demoState;
  if (!demo) return null;
  return (
    <article
      data-testid="self-learning-demo"
      className="mt-5 overflow-hidden border border-mint/35 bg-[radial-gradient(circle_at_top_left,rgba(124,240,166,0.16),rgba(8,17,31,0.92)_46%,rgba(2,6,23,0.97))] p-4"
    >
      <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.18em] text-mint">
            <Sparkles className="size-4" />
            <span>Self-Learning Demo</span>
            <span className="border border-mint/25 bg-mint/10 px-2 py-1">{demo.completed ? "completed" : "running"}</span>
          </div>
          <h3 className="mt-2 text-xl font-semibold text-white">Company conditions changed, AI adapted its strategy</h3>
          <p className="mt-2 text-sm leading-6 text-slate-400">{demo.executiveExplanation}</p>
        </div>
        <div className="grid min-w-72 grid-cols-3 gap-2">
          <MiniMetric label="Before" value={demo.initialPrediction} />
          <MiniMetric label="After" value={demo.adaptedPrediction} />
          <MiniMetric label="Delta" value={demo.predictionDelta} />
        </div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {demo.detectedChanges.map((change) => (
          <div key={change.metric} className="border border-line/60 bg-void/35 p-3">
            <p className="text-[10px] uppercase text-cyan">{change.sourceSystem.replaceAll("_", " ")}</p>
            <h4 className="mt-1 text-sm font-semibold text-white">{change.metric}</h4>
            <div className="mt-2 flex items-end justify-between gap-3">
              <span className="text-xs text-slate-500">{Math.round(change.beforeValue)} to {Math.round(change.afterValue)}</span>
              <strong className={change.changePercent < 0 ? "text-rose" : "text-amber"}>{change.changePercent.toFixed(1)}%</strong>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="grid gap-2">
          {demo.stages.map((stage) => (
            <div key={stage.stage} className="border border-line/60 bg-panel2/55 p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="grid size-7 place-items-center border border-mint/30 bg-mint/10 text-xs font-semibold text-mint">{stage.stage}</span>
                  <h4 className="text-sm font-semibold text-white">{stage.title}</h4>
                </div>
                <span className="border border-mint/25 bg-mint/10 px-2 py-1 text-[10px] uppercase text-mint">{stage.status}</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-400">{stage.explanation}</p>
              <div className="mt-2 flex flex-wrap gap-1">
                {stage.evidence.slice(0, 4).map((item) => (
                  <span key={`${stage.stage}-${item}`} className="border border-cyan/15 bg-cyan/10 px-2 py-1 text-[10px] text-cyan">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="grid gap-3">
          <div className="border border-line/60 bg-panel2/55 p-3">
            <p className="text-xs uppercase tracking-[0.16em] text-mint">Strategy Evolution</p>
            <p className="mt-3 text-xs leading-5 text-slate-500">{demo.previousStrategy}</p>
            <p className="mt-3 border border-mint/20 bg-mint/10 p-2 text-sm leading-6 text-white">{demo.evolvedStrategy}</p>
            {demo.strategyEvolution.map((item) => (
              <p key={item.reason} className="mt-2 text-xs leading-5 text-slate-400">
                {item.reason} Expected improvement: {Math.round(item.expectedImprovement)}%.
              </p>
            ))}
          </div>

          <div className="border border-line/60 bg-panel2/55 p-3">
            <p className="text-xs uppercase tracking-[0.16em] text-cyan">Learning Signals</p>
            <div className="mt-3 grid gap-2">
              {[...demo.activeDriftTypes, ...demo.retrainedModels.slice(0, 3), ...demo.digitalTwinSignals.slice(0, 3), ...demo.agentLearningUpdates.slice(0, 2)].map((item) => (
                <p key={item} className="border border-line/60 bg-void/35 p-2 text-xs leading-5 text-slate-400">{item}</p>
              ))}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/55 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
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
        <Icon className="size-4 text-mint" />
        <span>{label}</span>
      </div>
      <strong className="mt-2 block break-words text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function MiniMetric({ label, value, suffix = "" }: { label: string; value?: number; suffix?: string }) {
  return (
    <div className="border border-line/60 bg-panel/50 p-2">
      <span className="text-[10px] uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{typeof value === "number" ? `${Math.round(value)}${suffix}` : "verifying"}</strong>
    </div>
  );
}

function toCamel<T>(value: unknown): T {
  if (Array.isArray(value)) return value.map((item) => toCamel(item)) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as SnakeRecord).map(([key, nested]) => [
        key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase()),
        toCamel(nested),
      ]),
    ) as T;
  }
  return value as T;
}
