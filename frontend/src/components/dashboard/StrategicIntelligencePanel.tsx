"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Building2, GitBranch, Handshake, Lightbulb, Radar, RefreshCw, ShieldCheck, UsersRound } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type React from "react";

import type { RiskLevel, StrategicIntelligenceResponse } from "@/types/strategic";

type SnakeRecord = Record<string, unknown>;

const riskColor: Record<RiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function StrategicIntelligencePanel() {
  const [analysis, setAnalysis] = useState<StrategicIntelligenceResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/strategic/enterprise", { cache: "no-store" });
      if (!response.ok) throw new Error("Strategic intelligence failed");
      setAnalysis((await response.json()) as StrategicIntelligenceResponse);
    } catch {
      setError("Strategic intelligence graph could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runCrisis = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/strategic/enterprise", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(strategicCrisisPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Strategic intelligence failed");
      setAnalysis((await response.json()) as StrategicIntelligenceResponse);
    } catch {
      setError("Strategic crisis simulation could not complete.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/strategic/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing strategic stream");
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
              setAnalysis(toCamel<StrategicIntelligenceResponse>(JSON.parse(dataLine.slice(6))));
              setLoading(false);
            }
          }
        }
        setStreamStatus("ready");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("fallback");
      }
    }

    const firstRefresh = window.setTimeout(() => {
      void loadDefault();
    }, 600);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 9000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadDefault]);

  const competitorChart = useMemo(
    () =>
      analysis?.competitiveIntelligence.map((item) => ({
        name: shortName(item.competitor),
        pressure: Math.round(item.marketPressureScore),
      })) ?? [],
    [analysis],
  );

  const clientChart = useMemo(
    () =>
      analysis?.clientRelationshipIntelligence.map((item) => ({
        name: shortName(item.clientName),
        churn: Math.round(item.churnRisk),
        escalation: Math.round(item.escalationRisk),
      })) ?? [],
    [analysis],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Radar className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Strategic Intelligence Graph</p>
            <h2 className="text-xl font-semibold text-white">Competitors, clients, talent marketplace, org design, crisis response, and innovation AI</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <button onClick={() => void runCrisis()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            <AlertTriangle className="size-4" />
            Run crisis
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Synchronizing strategic market, client, talent, and crisis intelligence...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Market threats" value={String(analysis.summary.competitorThreats)} />
            <Stat label="Client risks" value={String(analysis.summary.highRiskClients)} />
            <Stat label="Talent matches" value={String(analysis.summary.marketplaceMatches)} />
            <Stat label="Mentors" value={String(analysis.summary.mentorMatches)} />
            <Stat label="Org changes" value={String(analysis.summary.orgUnitsToRestructure)} />
            <Stat label="Innovators" value={String(analysis.summary.innovationLeaders)} />
            <Stat label="Crisis" value={`${Math.round(analysis.summary.crisisSeverity)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 border border-line/70 bg-panel2/65 p-4">
            <div className="flex items-start gap-3">
              <ShieldCheck className="mt-1 size-4 text-mint" />
              <p className="text-sm leading-6 text-slate-300">{analysis.executiveBrief}</p>
            </div>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <ChartPanel title="Competitive pressure" icon={Radar}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={competitorChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="pressure" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>

            <ChartPanel title="Client relationship risk" icon={Handshake}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={clientChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="churn" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="escalation" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={UsersRound} label="Internal talent marketplace" />
              <div className="grid gap-3">
                {analysis.internalMarketplaceMatches.slice(0, 4).map((match) => (
                  <div key={`${match.employeeId}-${match.projectId}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{match.employeeName}</h3>
                      <span className="text-xs text-cyan">{Math.round(match.matchScore)} match</span>
                    </div>
                    <p className="mt-1 text-xs uppercase text-mint">{match.projectTitle}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{match.rationale}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={GitBranch} label="Organization optimizer and crisis plan" />
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.organizationOptimizations.slice(0, 2).map((unit) => (
                  <div key={unit.unit} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{unit.unit}</h3>
                      <span className="text-xs text-amber">{Math.round(unit.optimizationPressure)} pressure</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{unit.reportingChange}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 border border-signal/30 bg-signal/10 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-medium text-white">{analysis.crisisResponse.scenario}</span>
                  <span className="text-xs uppercase" style={{ color: riskColor[analysis.crisisResponse.riskLevel] }}>
                    {analysis.crisisResponse.riskLevel}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-300">{analysis.crisisResponse.recoveryPriorities[0]}</p>
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Lightbulb} label="Innovation detector" />
              <div className="grid gap-3 sm:grid-cols-2">
                {analysis.innovationSignals.slice(0, 4).map((signal) => (
                  <div key={signal.employeeId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{signal.employeeName}</h3>
                      <span className="text-xs text-mint">{Math.round(signal.innovationScore)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{signal.sponsorshipAction}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <SectionTitle icon={Building2} label="Market and client actions" />
              <div className="grid gap-3">
                {analysis.competitiveIntelligence.slice(0, 2).map((item) => (
                  <div key={item.competitor} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{item.competitor}</h3>
                      <span className="text-xs uppercase" style={{ color: riskColor[item.threatLevel] }}>
                        {item.threatLevel}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{item.recommendedResponse}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function ChartPanel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <SectionTitle icon={Icon} label={title} />
      <div className="h-72">{children}</div>
    </article>
  );
}

function SectionTitle({ icon: Icon, label }: { icon: LucideIcon; label: string }) {
  return (
    <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      {label}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function shortName(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .join(" ");
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

function strategicCrisisPayload() {
  return {
    crisis_scenario: "competitor launch, executive client escalation, and platform talent shortage",
    competitors: [
      {
        name: "HelixOps AI",
        hiring_velocity: 48,
        product_launches_90d: 4,
        ai_mentions_30d: 122,
        funding_signal: 0.92,
        security_incidents: 1,
        technology_adoption_score: 91,
        market_sentiment: 0.66,
      },
    ],
    clients: [
      {
        client_id: "client-orion",
        name: "Orion Global Bank",
        contract_value: 4800000,
        delivery_slippage_days: 29,
        sentiment_score: -0.62,
        payment_delay_days: 18,
        escalation_count: 7,
        usage_trend_percent: -28,
        executive_engagement_score: 31,
      },
    ],
    talent: [
      {
        employee_id: "emp-lina",
        name: "Lina Chen",
        role: "Platform Engineer",
        department: "Engineering",
        skills: ["python", "kubernetes", "mlops", "incident response", "redis"],
        mentor_topics: ["kubernetes", "incident response", "mlops"],
        capacity_hours: 40,
        allocated_hours: 30,
        stress_score: 42,
        leadership_score: 79,
        innovation_signals: 6,
      },
      {
        employee_id: "emp-nisha",
        name: "Nisha Rao",
        role: "Security Architect",
        department: "Security",
        skills: ["security", "zero trust", "python", "threat modeling", "kubernetes"],
        mentor_topics: ["security", "threat modeling", "zero trust"],
        capacity_hours: 40,
        allocated_hours: 37,
        stress_score: 58,
        leadership_score: 87,
        innovation_signals: 7,
      },
    ],
    projects: [
      {
        project_id: "proj-market-defense",
        title: "Competitive AI Defense Room",
        department: "Strategy",
        required_skills: ["python", "mlops", "kubernetes", "api reliability"],
        priority: 5,
        revenue_impact: 6200000,
        deadline_pressure: 84,
      },
      {
        project_id: "proj-zero-trust",
        title: "Zero Trust Data Export Guardrails",
        department: "Security",
        required_skills: ["security", "zero trust", "threat modeling", "kubernetes"],
        priority: 4,
        revenue_impact: 2900000,
        deadline_pressure: 63,
      },
    ],
    org_units: [
      {
        unit: "Engineering Platform",
        headcount: 42,
        manager_count: 3,
        dependency_load: 88,
        stress_score: 77,
        collaboration_score: 58,
        decision_latency_days: 10,
        critical_skills_gap: 6,
      },
    ],
  };
}
