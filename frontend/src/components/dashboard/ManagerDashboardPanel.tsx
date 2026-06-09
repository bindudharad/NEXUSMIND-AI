"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { AlertTriangle, BriefcaseBusiness, RefreshCw, ShieldAlert, Users, Workflow } from "lucide-react";

import type { ManagerDashboardResponse, ManagerRiskSeverity } from "@/types/manager-dashboard";

const severityColor: Record<ManagerRiskSeverity, string> = {
  critical: "#F05D5E",
  high: "#F6B44B",
  medium: "#2EE9D3",
  low: "#7CF0A6",
};

export function ManagerDashboardPanel() {
  const [dashboard, setDashboard] = useState<ManagerDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshCount, setRefreshCount] = useState(0);
  const [error, setError] = useState("");
  const activeMode = useRef<"default" | "crisis">("default");

  async function loadDashboard(mode: "default" | "crisis" = "default") {
    activeMode.current = mode;
    setLoading(true);
    setError("");
    try {
      const response =
        mode === "default"
          ? await fetch("/api/managers/dashboard", { cache: "no-store" })
          : await fetch("/api/managers/dashboard", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                manager_id: "mgr-crisis",
                manager_name: "Priya Raman",
                sensitivity: 0.72,
                teams: [
                  {
                    team_id: "team-dev-crisis",
                    team_name: "Development Team",
                    department: "Engineering",
                    member_count: 22,
                    burnout_probability: 0.92,
                    productivity_decline: 0.74,
                    average_stress: 0.9,
                    toxicity_ratio: 0.31,
                    overload_ratio: 0.88,
                    missed_deadlines: 11,
                    attendance_rate: 0.78,
                    collaboration_score: 0.49,
                    overtime_escalation: 0.88,
                    dependency_bottlenecks: 12,
                  },
                  {
                    team_id: "team-platform-crisis",
                    team_name: "Platform Reliability",
                    department: "Engineering",
                    member_count: 12,
                    burnout_probability: 0.61,
                    productivity_decline: 0.34,
                    average_stress: 0.68,
                    toxicity_ratio: 0.1,
                    overload_ratio: 0.52,
                    missed_deadlines: 4,
                    attendance_rate: 0.9,
                    collaboration_score: 0.7,
                    overtime_escalation: 0.44,
                    dependency_bottlenecks: 5,
                  },
                ],
                employees: [
                  {
                    employee_id: "emp-john",
                    employee_name: "Employee John",
                    team_name: "Development Team",
                    role: "Backend Lead",
                    active_tasks: 24,
                    overtime_hours: 22,
                    meeting_hours: 16,
                    productivity_score: 0.44,
                    work_intensity: 0.96,
                    deadline_pressure: 0.94,
                    multi_project_allocation: 7,
                    stress_score: 0.93,
                    task_completion_ratio: 0.43,
                  },
                  {
                    employee_id: "emp-nina",
                    employee_name: "Employee Nina",
                    team_name: "Development Team",
                    role: "QA Lead",
                    active_tasks: 18,
                    overtime_hours: 15,
                    meeting_hours: 11,
                    productivity_score: 0.59,
                    work_intensity: 0.86,
                    deadline_pressure: 0.82,
                    multi_project_allocation: 5,
                    stress_score: 0.81,
                    task_completion_ratio: 0.57,
                  },
                ],
                projects: [
                  {
                    project_id: "project-alpha",
                    project_name: "Project Alpha",
                    team_name: "Development Team",
                    task_completion_speed: 0.31,
                    team_productivity_trend: -0.72,
                    historical_delivery_rate: 0.48,
                    burnout_growth: 0.86,
                    team_overload: 0.91,
                    dependency_bottlenecks: 13,
                    resource_shortage: 0.72,
                    communication_efficiency: 0.38,
                    scope_change_rate: 0.66,
                    days_to_deadline: 9,
                  },
                ],
              }),
            });
      if (!response.ok) throw new Error("Leadership intelligence request failed");
      setDashboard((await response.json()) as ManagerDashboardResponse);
      setRefreshCount((current) => current + 1);
    } catch {
      setError("Leadership intelligence telemetry could not refresh.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const firstRefresh = window.setTimeout(() => {
      void loadDashboard();
    }, 5800);
    const interval = window.setInterval(() => {
      void loadDashboard(activeMode.current);
    }, 15000);
    return () => {
      window.clearTimeout(firstRefresh);
      window.clearInterval(interval);
    };
  }, []);

  const teamChart = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.riskyTeams.map((team) => ({
      name: team.teamName,
      score: team.riskScore,
      severity: team.severity,
    }));
  }, [dashboard]);

  const trendChart = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.trend.map((point) => ({
      day: new Date(point.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      teamRisk: point.averageTeamRisk,
      overload: point.overloadPressure,
      delay: point.delayRisk,
    }));
  }, [dashboard]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <BriefcaseBusiness className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Leadership Intelligence Console</p>
            <h2 className="text-xl font-semibold text-white">Team stability, capacity pressure, and delivery-risk predictions</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => void loadDashboard("default")}
            className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300"
          >
            <RefreshCw className="size-4" />
            Refresh live
          </button>
          <button
            onClick={() => void loadDashboard("crisis")}
            className="inline-flex items-center gap-2 border border-signal/40 bg-signal/10 px-3 py-2 text-sm text-signal"
          >
            <AlertTriangle className="size-4" />
            Simulate delivery crisis
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-6 text-sm text-slate-400">Refreshing leadership AI telemetry...</p> : null}

      {dashboard ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-5">
            <Stat label="Model" value={dashboard.model} />
            <Stat label="Teams at Risk" value={String(dashboard.summary.teamsAtRisk)} />
            <Stat label="Capacity pressure" value={String(dashboard.summary.overloadedEmployees)} />
            <Stat label="Delay Risks" value={String(dashboard.summary.projectsAtDelayRisk)} />
            <Stat label="Refresh" value={`#${refreshCount}`} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
            <div className="h-72 border border-line/70 bg-panel2/65 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={teamChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="score" radius={[3, 3, 0, 0]}>
                    {teamChart.map((entry) => (
                      <Cell key={`${entry.name}-${entry.score}`} fill={severityColor[entry.severity]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              {dashboard.riskyTeams.slice(0, 2).map((team) => (
                <article key={team.teamId} className="border border-line/70 bg-panel2/65 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs uppercase text-slate-500">Risky team / {team.severity}</p>
                      <h3 className="mt-1 text-lg font-semibold text-white">{team.teamName}</h3>
                    </div>
                    <span className="border border-amber/35 bg-amber/10 px-2 py-1 text-xs text-amber">
                      {Math.round(team.riskScore)}/100
                    </span>
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {team.drivers.slice(0, 4).map((driver) => (
                      <span key={driver} className="border border-line/60 bg-panel/60 px-2 py-1 text-xs text-slate-300">
                        {driver}
                      </span>
                    ))}
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-300">{team.recommendation}</p>
                </article>
              ))}
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.9fr]">
            <div className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <Users className="size-4" />
                Overloaded employees
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-3">
                {dashboard.overloadedEmployees.slice(0, 3).map((employee) => (
                  <article key={employee.employeeId} className="border border-line/60 bg-panel/65 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="font-semibold text-white">{employee.employeeName}</h3>
                        <p className="mt-1 text-xs text-slate-500">{employee.teamName} / {employee.role}</p>
                      </div>
                      <span className="text-sm text-amber">{Math.round(employee.overloadScore)}%</span>
                    </div>
                    <p className="mt-3 text-xs leading-5 text-slate-300">{employee.recommendation}</p>
                  </article>
                ))}
              </div>
            </div>

            <div className="border border-line/70 bg-panel2/65 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-amber">
                <ShieldAlert className="size-4" />
                Delay prediction AI
              </div>
              <div className="mt-3 space-y-3">
                {dashboard.delayPredictions.slice(0, 3).map((project) => (
                  <article key={project.projectId} className="border border-line/60 bg-panel/65 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <h3 className="font-semibold text-white">{project.projectName}</h3>
                      <span className="text-sm text-signal">{Math.round(project.delayProbability)}%</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-500">{project.projectedDelayDays} projected delay days</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{project.recommendation}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <div className="h-72 border border-line/70 bg-panel2/65 p-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendChart} margin={{ left: -18, right: 8, top: 10, bottom: 0 }}>
                  <defs>
                    <linearGradient id="managerRiskGradient" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#2EE9D3" stopOpacity={0.28} />
                      <stop offset="95%" stopColor="#2EE9D3" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="day" stroke="#64748b" tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Area type="monotone" dataKey="teamRisk" stroke="#2EE9D3" fill="url(#managerRiskGradient)" strokeWidth={2} />
                  <Line type="monotone" dataKey="overload" stroke="#F6B44B" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="delay" stroke="#F05D5E" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="border border-cyan/25 bg-cyan/10 p-4">
              <div className="flex items-center gap-2 text-xs uppercase text-cyan">
                <Workflow className="size-4" />
                Manager recommendations
              </div>
              <div className="mt-3 space-y-2">
                {dashboard.recommendations.map((recommendation) => (
                  <p key={recommendation} className="border border-line/60 bg-panel/65 p-3 text-sm leading-6 text-slate-300">
                    {recommendation}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-lg text-white">{value}</strong>
    </div>
  );
}
