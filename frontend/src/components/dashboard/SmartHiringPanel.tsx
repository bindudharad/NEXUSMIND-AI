"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { BrainCircuit, BriefcaseBusiness, FileSearch, Loader2, Radio, RefreshCw, ShieldAlert, Sparkles, UserCheck } from "lucide-react";

import type { CandidateRanking, HiringResponse, HiringRiskLevel } from "@/types/hiring";

type SnakeRecord = Record<string, unknown>;

const severityColor: Record<HiringRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function SmartHiringPanel() {
  const [analysis, setAnalysis] = useState<HiringResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/hiring/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("Hiring analysis failed");
      setAnalysis((await response.json()) as HiringResponse);
    } catch {
      setError("Smart Hiring AI could not load recruiter intelligence.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runRecruiterStress = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/hiring/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recruiterStressPayload()),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Hiring analysis failed");
      setAnalysis((await response.json()) as HiringResponse);
    } catch {
      setError("Smart Hiring AI could not process the candidate slate.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/hiring/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing hiring stream");
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
              setAnalysis(toCamel<HiringResponse>(JSON.parse(dataLine.slice(6))));
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
    }, 7000);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 18500);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
    };
  }, [loadDefault]);

  const rankingChart = useMemo(
    () =>
      analysis?.rankings.map((candidate) => ({
        name: compactName(candidate.candidateName),
        compatibility: Math.round(candidate.compatibilityScore),
        skills: Math.round(candidate.skillMatchScore),
        risk: Math.round(candidate.hiringRiskScore),
      })) ?? [],
    [analysis],
  );

  const topCandidate = analysis?.rankings[0] ?? null;

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <FileSearch className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Smart Hiring AI</p>
            <h2 className="text-xl font-semibold text-white">Resume intelligence, semantic role matching, candidate ranking, and recruiter risk analytics</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh slate
          </button>
          <button onClick={() => void runRecruiterStress()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Rank candidates
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Running TF-IDF semantic matching, RandomForest ranking, skill-gap analysis, and fraud-risk checks...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Candidates" value={String(analysis.summary.candidatesAnalyzed)} />
            <Stat label="Avg fit" value={`${Math.round(analysis.summary.averageCompatibility)}%`} />
            <Stat label="Top candidate" value={compactName(analysis.summary.topCandidate)} />
            <Stat label="Strong hires" value={String(analysis.summary.strongHireCount)} />
            <Stat label="Fraud risks" value={String(analysis.summary.fraudRiskCount)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_0.92fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <BrainCircuit className="size-4" />
                Candidate ranking model
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={rankingChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="compatibility" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="skills" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="risk" fill="#FF3B6B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {analysis.rankings.map((candidate) => (
                  <CandidateCard key={candidate.candidateId} candidate={candidate} />
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <UserCheck className="size-4" />
                Top candidate intelligence
              </div>
              {topCandidate ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Signal label="Compatibility" value={topCandidate.compatibilityScore} color="#2EE9D3" />
                    <Signal label="Semantic match" value={topCandidate.semanticMatchScore} color="#7CF0A6" />
                    <Signal label="Skill match" value={topCandidate.skillMatchScore} color="#F6B44B" />
                    <Signal label="Hiring risk" value={topCandidate.hiringRiskScore} color="#FF3B6B" />
                  </div>
                  <div className="mt-4 border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2 text-xs uppercase">
                      <span className="text-slate-500">Recommendation</span>
                      <span className="text-cyan">{labelize(topCandidate.hiringRecommendation)}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{topCandidate.rankingExplanation[0]}</p>
                  </div>
                </>
              ) : null}
              <div className="mt-4 grid gap-2">
                {(topCandidate?.matchedSkills ?? []).slice(0, 8).map((skill) => (
                  <span key={skill} className="border border-cyan/30 bg-cyan/10 px-2 py-1 text-xs text-cyan">
                    {skill}
                  </span>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Fraud and evidence risk
              </div>
              <div className="grid gap-3">
                {analysis.rankings.flatMap((candidate) =>
                  candidate.fraudSignals.length
                    ? candidate.fraudSignals.map((signal) => (
                        <div key={`${candidate.candidateId}-${signal.signal}`} className="border border-line/60 bg-panel/60 p-3">
                          <div className="flex items-center justify-between gap-2">
                            <h3 className="text-sm font-medium text-white">{candidate.candidateName}</h3>
                            <span className="text-xs uppercase" style={{ color: severityColor[signal.severity] }}>
                              {signal.severity}
                            </span>
                          </div>
                          <p className="mt-2 text-xs leading-5 text-slate-400">{signal.evidence}</p>
                        </div>
                      ))
                    : [],
                )}
                {!analysis.rankings.some((candidate) => candidate.fraudSignals.length) ? (
                  <p className="border border-line/60 bg-panel/60 p-3 text-sm text-slate-400">No material resume fraud signals detected.</p>
                ) : null}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <BriefcaseBusiness className="size-4" />
                Recruiter recommendations
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {analysis.recommendations.map((recommendation) => (
                  <div key={recommendation.recommendationId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{recommendation.title}</h3>
                      <span className="text-xs text-cyan">{Math.round(recommendation.impactScore)} impact</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{recommendation.action}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{recommendation.rationale}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.8fr_1.2fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Radio className="size-4" />
                Recruiter analytics
              </div>
              <div className="grid gap-2">
                {analysis.recruiterTrends.map((trend) => (
                  <div key={trend.label} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2 text-sm">
                      <span className="text-white">{trend.label}</span>
                      <span style={{ color: severityColor[trend.severity] }}>{Math.round(trend.value)}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">{trend.explanation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Sparkles className="size-4" />
                Skill-gap heatmap
              </div>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                {analysis.skillGapHeatmap.length ? (
                  analysis.skillGapHeatmap.map((item) => (
                    <div key={String(item.skill)} className="border border-line/60 bg-panel/60 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm text-white">{labelize(String(item.skill))}</span>
                        <span className="text-xs text-amber">{String(item.severity)}</span>
                      </div>
                      <div className="mt-2 h-2 bg-void">
                        <div className="h-2 bg-amber" style={{ width: `${Math.min(100, Number(item.gapCount ?? item.gap_count ?? 0) * 30)}%` }} />
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-400">Top candidates cover all required skills.</p>
                )}
              </div>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}

function CandidateCard({ candidate }: { candidate: CandidateRanking }) {
  const color = candidate.compatibilityScore >= 80 ? "#7CF0A6" : candidate.compatibilityScore >= 65 ? "#2EE9D3" : candidate.compatibilityScore >= 48 ? "#F6B44B" : "#FF3B6B";
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-medium text-white">{candidate.candidateName}</h3>
          <p className="mt-1 text-xs text-slate-500">Rank #{candidate.rank}</p>
        </div>
        <span className="text-xs" style={{ color }}>
          {Math.round(candidate.compatibilityScore)}%
        </span>
      </div>
      <p className="mt-2 text-xs uppercase text-cyan">{labelize(candidate.hiringRecommendation)}</p>
      <p className="mt-2 text-xs text-slate-400">{candidate.missingSkills.length ? `${candidate.missingSkills.length} required gap(s)` : "Required skills covered"}</p>
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

function Signal({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold" style={{ color }}>
        {Math.round(value)}
      </p>
    </div>
  );
}

function compactName(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .join(" ");
}

function labelize(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
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

function recruiterStressPayload() {
  return {
    realtime: true,
    role: {
      role_id: "role-backend-ai-platform",
      title: "Backend AI Platform Engineer",
      job_description:
        "Build secure Python FastAPI services for enterprise AI, Kubernetes deployment automation, PostgreSQL and Redis reliability, MLOps model serving, incident response, and API observability.",
      required_skills: ["python", "kubernetes", "api reliability", "security", "postgresql"],
      preferred_skills: ["redis", "mlops", "incident response", "microservices", "testing"],
      seniority: "senior",
      team_context: "Enterprise AI platform team operating realtime analytics and model-serving APIs.",
      culture_values: ["ownership", "clear communication", "collaboration", "incident discipline"],
      domain_keywords: ["enterprise ai", "platform reliability", "secure api", "model serving"],
    },
    candidates: [
      {
        candidate_id: "cand-elite-hiring",
        candidate_name: "Mira Sen",
        current_title: "Senior Platform Engineer",
        years_experience: 9,
        expected_salary: 188000,
        declared_skills: ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Redis", "Security", "MLOps"],
        certifications: ["CKA", "AWS Solutions Architect"],
        resume_text:
          "Led Python FastAPI services for a model-serving platform, migrated workloads to Kubernetes, optimized PostgreSQL, added Redis caching, owned JWT security reviews, built observability, and reduced API latency by 41%. Mentored engineers and ran incident postmortems.",
        interview_transcript:
          "I clarify customer impact, communicate tradeoffs, document recovery steps, and pair with teammates during incidents. I care about ownership and clear handoffs.",
        portfolio_summary: "Built a secure MLOps gateway with canary deployments, tracing, rate limits, and model monitoring.",
      },
      {
        candidate_id: "cand-gap-hiring",
        candidate_name: "Dev Arora",
        current_title: "Backend Engineer",
        years_experience: 5,
        expected_salary: 136000,
        declared_skills: ["Python", "Django", "Docker", "SQL", "Testing"],
        certifications: [],
        resume_text:
          "Built Python APIs, Django services, Docker workflows, SQL reports, and automated tests. Supported production incidents and helped split a monolith into microservices.",
        interview_transcript: "I learn infrastructure quickly and communicate blockers early.",
        portfolio_summary: "Payment reconciliation API and CI test harness.",
      },
      {
        candidate_id: "cand-risk-hiring",
        candidate_name: "Fake Pattern Candidate",
        current_title: "Principal Everything Architect",
        years_experience: 3,
        expected_salary: 280000,
        declared_skills: ["Python", "Kubernetes", "Security", "MLOps", "AWS", "Leadership"],
        certifications: ["Self certified cloud expert"],
        resume_text:
          "Personally owned every architecture decision for dozens of unicorn-scale platforms and mastered all cloud, security, AI, Kubernetes, databases, frontend, backend, and leadership functions without team dependency. 20 years Kubernetes experience.",
        interview_transcript: "I prefer to work alone and do not need reviews or postmortems because I already know the answer.",
        portfolio_summary: "No public projects available.",
      },
    ],
  };
}
