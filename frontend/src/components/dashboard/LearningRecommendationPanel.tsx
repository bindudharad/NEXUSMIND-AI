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
import {
  Award,
  BookOpen,
  Brain,
  GraduationCap,
  Loader2,
  Map,
  Radio,
  RefreshCw,
  Send,
  ShieldAlert,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";

import type { LearningPriority, LearningResponse } from "@/types/learning";

const priorityColor: Record<LearningPriority, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function LearningRecommendationPanel() {
  const [analysis, setAnalysis] = useState<LearningResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const manualScenarioUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = 0;
    try {
      const payload = await fetchJson("/api/learning/recommend", { cache: "no-store" });
      if (!isLearningResponse(payload)) throw new Error("Malformed learning payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Learning Recommendation System could not refresh live workforce learning intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const simulateSkillGap = useCallback(async () => {
    setLoading(true);
    setError("");
    manualScenarioUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson(
        "/api/learning/recommend",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildLearningPayload()),
          cache: "no-store",
        },
        60000,
      );
      if (!isLearningResponse(payload)) throw new Error("Malformed learning payload");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Learning Recommendation System could not process the skill-gap scenario.");
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
        const response = await fetch("/api/learning/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Learning stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing learning stream");
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
            if (isLearningResponse(payload) && Date.now() > manualScenarioUntil.current) {
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

  const gapData = useMemo(
    () =>
      analysis?.skillGaps.slice(0, 8).map((item) => ({
        name: item.employeeName.split(" ")[0],
        gap: Math.round(item.gapScore),
        criticality: Math.round(item.futureCriticality),
        blocker: Math.round(item.promotionBlockerScore),
      })) ?? [],
    [analysis],
  );

  const heatmapData = useMemo(
    () =>
      analysis?.teamUpskillingHeatmap.slice(0, 9).map((item) => ({
        department: item.department,
        skill: titleCase(item.skill),
        gap: Math.round(item.gapScore),
        demand: Math.round(item.demandScore),
        readiness: Math.round(item.readinessScore),
        priority: item.priority,
      })) ?? [],
    [analysis],
  );

  const progressData = useMemo(
    () =>
      analysis?.progressForecasts.slice(0, 8).map((item) => ({
        skill: titleCase(item.targetSkill).slice(0, 14),
        mastery: Math.round(item.masteryProbability),
        certification: Math.round(item.certificationCompletionProbability),
        lift: Math.round(item.productivityLiftEstimate),
      })) ?? [],
    [analysis],
  );

  const topCourses = useMemo(() => analysis?.courseRecommendations.slice(0, 6) ?? [], [analysis]);
  const roadmap = useMemo(() => analysis?.careerRoadmaps.slice(0, 6) ?? [], [analysis]);
  const certifications = useMemo(
    () => analysis?.courseRecommendations.filter((item) => item.certification !== "Applied skill credential").slice(0, 5) ?? [],
    [analysis],
  );

  return (
    <section data-testid="learning-recommendation-panel" className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <GraduationCap className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Learning Recommendation System</p>
            <h2 className="text-xl font-semibold text-white">
              Skill-gap heatmaps, personalized course widgets, career roadmap visualizations, certification recommendation panels, team upskilling analytics, learning progress graphs, and executive workforce-learning insights
            </h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button data-testid="refresh-learning-recommendation" onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh plan
          </button>
          <button data-testid="simulate-learning-recommendation" onClick={() => void simulateSkillGap()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Simulate skill gap
          </button>
        </div>
      </div>

      {error && !analysis ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Ranking courses, modeling skill gaps, forecasting certifications, and building role-based learning roadmaps...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Learning signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Courses" value={String(analysis.summary.recommendationsGenerated)} />
            <Stat label="Critical gaps" value={String(analysis.summary.criticalSkillGaps)} />
            <Stat label="Avg gap" value={`${Math.round(analysis.summary.averageGapScore)}%`} />
            <Stat label="Completion" value={`${Math.round(analysis.summary.averageCompletionProbability)}%`} />
            <Stat label="Roadmaps" value={String(analysis.summary.promotionRoadmaps)} />
            <Stat label="Readiness" value={`${Math.round(analysis.summary.workforceReadinessScore)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Target className="size-4" />
                Skill-gap heatmaps
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={gapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="gap" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="criticality" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="blocker" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <BookOpen className="size-4" />
                Personalized course widgets
              </div>
              <div className="grid gap-2">
                {topCourses.map((course) => (
                  <div key={`${course.employeeId}-${course.courseId}-${course.targetSkill}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-white">{course.title}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {course.employeeName} · {course.provider} · {titleCase(course.targetSkill)}
                        </p>
                      </div>
                      <span className="text-sm font-semibold text-cyan">{Math.round(course.recommendationScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{course.rationale}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-[11px] uppercase text-slate-500">
                      <span className="border border-line/60 px-2 py-1">{course.difficulty}</span>
                      <span className="border border-line/60 px-2 py-1">{course.durationHours}h</span>
                      <span className="border border-line/60 px-2 py-1">{Math.round(course.completionProbability)}% completion</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.98fr_1.02fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Map className="size-4" />
                Career roadmap visualizations
              </div>
              <div className="grid gap-3">
                {roadmap.map((step) => (
                  <div key={`${step.employeeId}-${step.month}-${step.title}`} className="grid grid-cols-[64px_1fr] gap-3 border border-line/60 bg-panel/60 p-3">
                    <div>
                      <p className="text-xs uppercase text-slate-500">Month</p>
                      <p className="text-2xl font-semibold text-white">{step.month}</p>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{step.title}</p>
                      <p className="mt-1 text-xs text-slate-500">{step.employeeName} · {step.focusSkills.map(titleCase).join(", ")}</p>
                      <p className="mt-2 text-xs text-slate-400">{step.expectedOutcome}</p>
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Users className="size-4" />
                Team upskilling analytics
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={heatmapData} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="skill" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="gap" radius={[3, 3, 0, 0]}>
                      {heatmapData.map((item) => (
                        <Cell key={`${item.department}-${item.skill}`} fill={priorityColor[item.priority]} />
                      ))}
                    </Bar>
                    <Bar dataKey="demand" fill="#8B5CF6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="readiness" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <TrendingUp className="size-4" />
                Learning progress graphs
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={progressData} margin={{ left: -22, right: 10, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="skill" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Line type="monotone" dataKey="mastery" stroke="#2EE9D3" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="certification" stroke="#F6B44B" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="lift" stroke="#8B5CF6" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Award className="size-4" />
                Certification recommendation panels
              </div>
              <div className="space-y-3">
                {certifications.map((course, index) => (
                  <div key={`${course.employeeId}-${course.courseId}-${course.targetSkill}-${index}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-semibold text-white">{course.certification}</p>
                        <p className="mt-1 text-xs text-slate-500">{course.employeeName} · {course.provider}</p>
                      </div>
                      <span className="text-sm text-cyan">{Math.round(course.careerImpact)} impact</span>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <ShieldAlert className="size-4" />
                Realtime learning alerts
              </div>
              <div className="space-y-3">
                {analysis.learningAlerts.slice(0, 4).map((alert, index) => (
                  <div key={`${alert.title}-${index}`} className="border-l-2 bg-panel/60 p-3" style={{ borderColor: priorityColor[alert.priority] }}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{alert.title}</p>
                        <p className="mt-1 text-xs text-slate-400">{alert.impact}</p>
                      </div>
                      <span className="text-sm font-semibold" style={{ color: priorityColor[alert.priority] }}>
                        {Math.round(alert.probability)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Brain className="size-4" />
                Executive workforce-learning insights
              </div>
              <div className="grid gap-3">
                {analysis.executiveInsights.slice(0, 5).map((insight, index) => (
                  <p key={`${insight}-${index}`} className="border border-line/60 bg-panel/60 p-3 text-sm text-slate-300">
                    {insight}
                  </p>
                ))}
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] uppercase text-slate-500">
                <Radio className="size-3 text-cyan" />
                {analysis.model}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

async function fetchJson(input: string, init?: RequestInit, timeoutMs = 45000): Promise<unknown> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(input, { ...init, signal: controller.signal });
    const text = await response.text();
    const payload = text ? (JSON.parse(text) as unknown) : {};
    if (!response.ok) throw new Error("Learning request failed");
    return payload;
  } finally {
    window.clearTimeout(timeout);
  }
}

function isLearningResponse(payload: unknown): payload is LearningResponse {
  const value = payload as Partial<LearningResponse> | null;
  return Boolean(
    value &&
      typeof value.model === "string" &&
      Array.isArray(value.skillGaps) &&
      Array.isArray(value.courseRecommendations) &&
      Array.isArray(value.careerRoadmaps) &&
      Array.isArray(value.progressForecasts) &&
      Array.isArray(value.teamUpskillingHeatmap) &&
      Array.isArray(value.futureSkillForecasts) &&
      value.summary,
  );
}

function titleCase(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-1 block text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function buildLearningPayload() {
  return {
    cycle_name: "AI Platform Upskilling Intervention",
    horizon_months: 6,
    company_roadmap_skills: ["kubernetes", "mlops", "rag", "security", "system design", "vector search"],
    realtime: true,
    employees: [
      {
        employee_id: "learn-ui-gap",
        employee_name: "Employee A",
        role: "Backend Engineer",
        department: "Engineering",
        team: "Platform",
        current_skills: ["python", "fastapi"],
        target_role: "AI Platform Engineer",
        career_goal: "Own production AI reliability platforms",
        project_requirements: ["kubernetes", "mlops", "security", "system design"],
        future_project_skills: ["rag", "vector search", "mlops"],
        interests: ["cloud", "ai infrastructure"],
        performance_score: 88,
        productivity_score: 82,
        assessment_score: 70,
        promotion_readiness: 0.72,
        learning_velocity: 0.82,
        learning_hours_last_90d: 30,
        courses_completed_last_year: 4,
        manager_priority: 0.94,
        market_alignment: 0.9,
        attrition_risk: 0.42,
        burnout_risk: 0.34,
      },
      {
        employee_id: "learn-ui-ready",
        employee_name: "Employee B",
        role: "Cloud Architect",
        department: "Engineering",
        team: "Architecture",
        current_skills: ["kubernetes", "mlops", "security", "system design", "rag", "vector search"],
        target_role: "Principal Architect",
        career_goal: "Scale AI platform architecture",
        project_requirements: ["kubernetes", "security", "system design"],
        future_project_skills: ["rag", "mlops"],
        interests: ["architecture"],
        performance_score: 94,
        productivity_score: 91,
        assessment_score: 90,
        promotion_readiness: 0.84,
        learning_velocity: 0.68,
        learning_hours_last_90d: 18,
        courses_completed_last_year: 3,
        manager_priority: 0.62,
        market_alignment: 0.7,
        attrition_risk: 0.16,
        burnout_risk: 0.18,
      },
    ],
  };
}
