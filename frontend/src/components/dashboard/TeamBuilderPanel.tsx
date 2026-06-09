"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, GitBranch, Loader2, Network, RefreshCw, Send, ShieldAlert, UsersRound } from "lucide-react";

import type { ChemistryHeatmapCell, TeamBuilderResponse, TeamBuilderRiskAlert } from "@/types/team-builder";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<TeamBuilderRiskAlert["severity"], string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function TeamBuilderPanel() {
  const [analysis, setAnalysis] = useState<TeamBuilderResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/team-builder/generate", { cache: "no-store" });
      if (!response.ok) throw new Error("Team builder failed");
      setAnalysis((await response.json()) as TeamBuilderResponse);
    } catch {
      setError("AI Team Builder could not generate the optimized squad.");
    } finally {
      setLoading(false);
    }
  }, []);

  const optimizeSquad = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/team-builder/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(stressTeamPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Team builder failed");
      setAnalysis((await response.json()) as TeamBuilderResponse);
    } catch {
      setError("AI Team Builder could not optimize the custom squad.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/team-builder/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing team builder stream");
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
            if (dataLine) {
              setAnalysis(toCamel<TeamBuilderResponse>(JSON.parse(dataLine.slice(6))));
              setLoading(false);
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
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

  const topTeam = analysis?.optimizedTeams[0];
  const teamChart = useMemo(
    () =>
      analysis?.optimizedTeams.slice(0, 5).map((team) => ({
        team: team.teamId.replace("team-builder-", "T"),
        success: Math.round(team.projectedDeliverySuccess),
        conflict: Math.round(team.conflictProbability),
      })) ?? [],
    [analysis],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <UsersRound className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Team Builder</p>
            <h2 className="text-xl font-semibold text-white">Graph AI squad formation, skill balancing, leadership matching, and conflict forecasting</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh teams
          </button>
          <button onClick={() => void optimizeSquad()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Optimize squad
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Searching team combinations, relationship embeddings, skill coverage, burnout balance, and leadership fit...</p> : null}

      {analysis && topTeam ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-7">
            <Stat label="Talent signals" value={String(analysis.summary.employeesAnalyzed)} />
            <Stat label="Combos" value={String(analysis.summary.combinationsEvaluated)} />
            <Stat label="Best score" value={`${Math.round(analysis.summary.bestTeamScore)}%`} />
            <Stat label="Skill cover" value={`${Math.round(topTeam.skillCoverage)}%`} />
            <Stat label="Conflict" value={`${Math.round(topTeam.conflictProbability)}%`} />
            <Stat label="Graph edges" value={String(analysis.summary.graphEdges)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <BrainCircuit className="size-4" />
                Optimized project squad
              </div>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h3 className="text-lg font-semibold text-white">{topTeam.title}</h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">{topTeam.rationale}</p>
                </div>
                <div className="border border-cyan/40 bg-cyan/10 px-3 py-2 text-right">
                  <span className="block text-xs uppercase text-cyan">Delivery success</span>
                  <strong className="text-2xl text-white">{Math.round(topTeam.projectedDeliverySuccess)}%</strong>
                </div>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {topTeam.members.map((member) => (
                  <div key={member.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h4 className="text-sm font-medium text-white">{member.name}</h4>
                        <p className="text-xs text-slate-400">{member.role}</p>
                      </div>
                      <span className="text-xs text-cyan">{Math.round(member.leadershipInfluence)}</span>
                    </div>
                    <p className="mt-2 text-xs uppercase text-mint">{member.graphCluster}</p>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {member.skills.slice(0, 4).map((skill) => (
                        <span key={`${member.employeeId}-${skill}`} className="bg-void/80 px-2 py-1 text-[11px] text-slate-300">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-2 text-sm leading-6 text-slate-300">
                {topTeam.recommendations.slice(0, 4).map((recommendation) => (
                  <p key={recommendation} className="border border-line/50 bg-panel/55 px-3 py-2">
                    {recommendation}
                  </p>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <GitBranch className="size-4" />
                Team generation model
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={teamChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="team" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="success" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="conflict" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid gap-2">
                <Signal label="Compatibility" value={topTeam.compatibilityScore} />
                <Signal label="Chemistry" value={topTeam.chemistryScore} />
                <Signal label="Burnout balance" value={topTeam.burnoutBalance} />
                <Signal label="Graph confidence" value={topTeam.graphConfidence * 100} />
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Network className="size-4" />
                Skill balance and leadership
              </div>
              <div className="grid gap-2">
                {analysis.skillBalance.map((skill) => (
                  <div key={skill.skill} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{skill.skill}</h3>
                      <span className="text-xs uppercase text-cyan">{skill.gapRisk} / {Math.round(skill.coverageScore)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{skill.recommendation}</p>
                    <p className="mt-2 text-xs text-mint">{skill.owners.length ? skill.owners.join(", ") : "No owner"}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-2 md:grid-cols-2">
                {analysis.leadershipRecommendations.slice(0, 4).map((leader) => (
                  <div key={leader.leaderName} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{leader.leaderName}</h3>
                      <span className="text-xs text-cyan">{Math.round(leader.leadershipScore)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{leader.scope}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Chemistry heatmap and conflict alerts
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {analysis.chemistryHeatmap.slice(0, 9).map((cell) => (
                  <HeatCell key={`${cell.source}-${cell.target}`} cell={cell} />
                ))}
              </div>
              <div className="mt-4 grid gap-3">
                {analysis.riskAlerts.map((alert) => (
                  <div key={`${alert.title}-${alert.members.join("-")}-${alert.probability}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{alert.members.join(" + ")}</h3>
                      <span style={{ color: severityColor[alert.severity] }} className="text-xs uppercase">
                        {alert.severity} / {Math.round(alert.probability)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{alert.intervention}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-2 text-sm leading-6 text-slate-300">
                {analysis.collaborationAnalytics.slice(0, 5).map((item) => (
                  <p key={item} className="border border-line/50 bg-panel/55 px-3 py-2">
                    {item}
                  </p>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function HeatCell({ cell }: { cell: ChemistryHeatmapCell }) {
  const color = cell.conflictProbability >= 48 ? "#FF3B6B" : cell.compatibilityScore >= 74 ? "#2EE9D3" : "#F6B44B";
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-white">{initials(cell.source)} + {initials(cell.target)}</span>
        <span className="text-xs" style={{ color }}>{Math.round(cell.compatibilityScore)}%</span>
      </div>
      <div className="mt-2 h-2 bg-void">
        <div className="h-2" style={{ width: `${Math.round(cell.compatibilityScore)}%`, background: color }} />
      </div>
      <p className="mt-2 text-xs text-slate-500">conflict {Math.round(cell.conflictProbability)} / graph {Math.round(cell.graphAttention * 100)}</p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block break-words text-base text-white">{value}</strong>
    </div>
  );
}

function Signal({ label, value }: { label: string; value: number }) {
  const rounded = Math.round(value);
  const color = rounded >= 75 ? "#7CF0A6" : rounded >= 55 ? "#F6B44B" : "#FF3B6B";
  return (
    <div>
      <div className="flex items-center justify-between gap-2 text-xs text-slate-400">
        <span>{label}</span>
        <span style={{ color }}>{rounded}%</span>
      </div>
      <div className="mt-1 h-2 bg-void">
        <div className="h-2" style={{ width: `${Math.min(100, Math.max(0, rounded))}%`, background: color }} />
      </div>
    </div>
  );
}

function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
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

function stressTeamPayload() {
  return {
    project_name: "Enterprise AI Launch Squad",
    project_type: "mission_critical_platform",
    required_skills: ["python", "api", "mlops", "testing", "ui", "devops"],
    target_team_size: 5,
    priority: "balanced",
    deadline_pressure: 0.64,
    employees: [
      teamMember("tm-backend", "Isha Menon", "Senior Backend Developer", "Engineering", ["python", "api", "security"], "analytical", 0.9, 0.24, 0.84, 0.88),
      teamMember("tm-ml", "Rahul Sen", "ML Engineer", "AI", ["python", "mlops", "forecasting"], "creative", 0.87, 0.3, 0.64, 0.8),
      teamMember("tm-ui", "Leena Rao", "UI/UX Designer", "Design", ["ux research", "dashboard", "product design", "accessibility"], "collaborative", 0.86, 0.28, 0.55, 0.9),
      teamMember("tm-qa", "Arun Das", "QA Engineer", "Quality", ["testing", "automation", "api"], "focused", 0.88, 0.27, 0.58, 0.78),
      teamMember("tm-devops", "Bianca Shah", "DevOps Engineer", "Platform", ["kubernetes", "devops", "security", "mlops"], "supportive", 0.91, 0.22, 0.7, 0.86),
      teamMember("tm-risk", "Crisis Owner", "Incident Commander", "Engineering", ["incident response", "api"], "decisive", 0.52, 0.88, 0.72, 0.35),
    ],
    interactions: [
      interaction("tm-backend", "tm-devops", 0.94, 0.91, 0.88, 0, 24),
      interaction("tm-backend", "tm-ml", 0.86, 0.85, 0.81, 0, 15),
      interaction("tm-ui", "tm-qa", 0.82, 0.8, 0.78, 0, 12),
      interaction("tm-risk", "tm-ui", 0.31, 0.35, 0.28, 5, 16),
    ],
    realtime: true,
  };
}

function teamMember(
  employeeId: string,
  name: string,
  role: string,
  department: string,
  skills: string[],
  workStyle: string,
  productivity: number,
  burnout: number,
  leadership: number,
  collaboration: number,
) {
  return {
    employee_id: employeeId,
    name,
    role,
    department,
    skills,
    work_style: workStyle,
    productivity_history: [productivity - 0.02, productivity, productivity + 0.01],
    stress_history: [burnout, Math.min(1, burnout + 0.03), Math.max(0, burnout - 0.02)],
    sentiment_trend: burnout > 0.7 ? -0.58 : 0.34,
    task_completion_rate: productivity,
    meeting_participation: workStyle === "collaborative" ? 0.72 : workStyle === "decisive" ? 0.86 : 0.48,
    collaboration_frequency: collaboration,
    leadership_score: leadership,
    burnout_risk: burnout,
    current_workload: burnout > 0.7 ? 0.94 : 0.58,
    focus_ratio: workStyle === "focused" ? 0.82 : 0.66,
  };
}

function interaction(sourceId: string, targetId: string, collaboration: number, success: number, sentiment: number, conflict: number, meetings: number) {
  return {
    source_id: sourceId,
    target_id: targetId,
    collaboration_frequency: collaboration,
    past_success_rate: success,
    sentiment_alignment: sentiment,
    conflict_incidents: conflict,
    meetings_together: meetings,
  };
}
