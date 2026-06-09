"use client";

import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, Check, GitBranch, HeartPulse, RefreshCw, Shuffle } from "lucide-react";

import type { RecommendationResponse } from "@/types/recommendations";

const categoryLabel = {
  work_redistribution: "Work redistribution",
  break: "Break",
  team_balancing: "Team balancing",
};

const categoryColor = {
  work_redistribution: "#2EE9D3",
  break: "#F6B44B",
  team_balancing: "#7CF0A6",
};

export function RecommendationAIPanel() {
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackId, setFeedbackId] = useState("");
  const [error, setError] = useState("");

  async function loadRecommendations(mode: "default" | "overload" = "default") {
    setLoading(true);
    setError("");
    try {
      const response =
        mode === "default"
          ? await fetch("/api/recommendations/generate", { cache: "no-store" })
          : await fetch("/api/recommendations/generate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                employees: [
                  {
                    employee_id: "emp-over",
                    name: "Employee A",
                    role: "Backend Lead",
                    team: "Core Systems",
                    skills: ["python", "api", "kubernetes"],
                    current_tasks: 14,
                    capacity_hours: 40,
                    allocated_hours: 64,
                    productivity: 0.66,
                    overtime_hours: 17,
                    stress_score: 0.91,
                    burnout_risk: 0.84,
                    collaboration_score: 0.72,
                  },
                  {
                    employee_id: "emp-ready",
                    name: "Employee B",
                    role: "Platform Engineer",
                    team: "Automation",
                    skills: ["python", "api", "workflow"],
                    current_tasks: 3,
                    capacity_hours: 40,
                    allocated_hours: 24,
                    productivity: 0.93,
                    overtime_hours: 1,
                    stress_score: 0.19,
                    burnout_risk: 0.12,
                    collaboration_score: 0.91,
                  },
                  {
                    employee_id: "emp-design",
                    name: "Employee C",
                    role: "Product Engineer",
                    team: "Experience",
                    skills: ["frontend", "workflow"],
                    current_tasks: 5,
                    capacity_hours: 38,
                    allocated_hours: 31,
                    productivity: 0.86,
                    overtime_hours: 3,
                    stress_score: 0.35,
                    burnout_risk: 0.21,
                    collaboration_score: 0.88,
                  },
                ],
                tasks: [
                  {
                    task_id: "task-api",
                    title: "payments API hardening",
                    required_skill: "python",
                    effort_hours: 9,
                    priority: 5,
                    project: "Revenue Platform",
                  },
                  {
                    task_id: "task-workflow",
                    title: "workflow rules engine",
                    required_skill: "workflow",
                    effort_hours: 7,
                    priority: 4,
                    project: "Autonomous Ops",
                  },
                ],
              }),
            });
      if (!response.ok) throw new Error("Recommendation request failed");
      setResult((await response.json()) as RecommendationResponse);
    } catch {
      setError("Recommendation AI could not produce a decision set.");
    } finally {
      setLoading(false);
    }
  }

  async function sendFeedback(recommendationId: string) {
    setFeedbackId(recommendationId);
    await fetch("/api/recommendations/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recommendation_id: recommendationId, accepted: true, usefulness_score: 5 }),
    });
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadRecommendations();
    }, 7800);
    return () => window.clearTimeout(timer);
  }, []);

  const chartData = useMemo(() => {
    if (!result) return [];
    return result.recommendations.map((item) => ({
      name: categoryLabel[item.category],
      impact: item.impactScore,
      category: item.category,
    }));
  }, [result]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BrainCircuit className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Recommendation AI</p>
            <h2 className="text-xl font-semibold text-white">Adaptive workload, wellness, and team balancing engine</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadRecommendations("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Baseline
          </button>
          <button
            onClick={() => void loadRecommendations("overload")}
            className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan"
          >
            <Shuffle className="size-4" />
            Simulate overload
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-6 text-sm text-slate-400">Ranking interventions with Random Forest impact scoring...</p> : null}

      {result ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4">
            <Stat label="Model" value={result.model} />
            <Stat label="Workforce signals" value={String(result.employeesAnalyzed)} />
            <Stat label="Task Graph" value={`${result.tasksAnalyzed} active`} />
            <Stat label="Balance Score" value={`${Math.round(result.teamBalanceScore)}%`} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.82fr_1.18fr]">
            <div className="h-72 border border-line/70 bg-panel2/65 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="impact" radius={[3, 3, 0, 0]}>
                    {chartData.map((entry) => (
                      <Cell key={`${entry.name}-${entry.impact}`} fill={categoryColor[entry.category]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-3">
              {result.recommendations.slice(0, 4).map((item) => (
                <article key={item.recommendationId} className="border border-line/70 bg-panel2/65 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <CategoryIcon category={item.category} />
                      <div>
                        <p className="text-xs uppercase text-slate-500">
                          {categoryLabel[item.category]} / {item.priority}
                        </p>
                        <h3 className="mt-1 text-base font-semibold text-white">{item.title}</h3>
                      </div>
                    </div>
                    <span className="border border-cyan/30 bg-cyan/10 px-2 py-1 text-xs text-cyan">
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{item.action}</p>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{item.rationale}</p>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
                    <span className="text-xs uppercase text-amber">
                      Impact {Math.round(item.impactScore)} / {item.sourceModel}
                    </span>
                    <button
                      onClick={() => void sendFeedback(item.recommendationId)}
                      className="inline-flex items-center gap-2 border border-mint/35 bg-mint/10 px-3 py-2 text-xs text-mint"
                    >
                      <Check className="size-3.5" />
                      {feedbackId === item.recommendationId ? "Learning captured" : "Accept signal"}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function CategoryIcon({ category }: { category: RecommendationResponse["recommendations"][number]["category"] }) {
  const className = "mt-1 size-4 text-cyan";
  if (category === "break") return <HeartPulse className={className} />;
  if (category === "team_balancing") return <GitBranch className={className} />;
  return <Shuffle className={className} />;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-lg text-white">{value}</strong>
    </div>
  );
}
