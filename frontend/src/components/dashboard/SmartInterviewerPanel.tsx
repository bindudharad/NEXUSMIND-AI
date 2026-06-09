"use client";

import {
  Bot,
  FileText,
  Loader2,
  Mic2,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
  UserCheck,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type {
  CandidateInterviewRanking,
  HiringDecision,
  InterviewRiskLevel,
  SmartInterviewAssistantResponse,
  SmartInterviewerResponse,
} from "@/types/smart-interviewer";

const riskColor: Record<InterviewRiskLevel, string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

const decisionColor: Record<HiringDecision, string> = {
  strong_hire: "#7CF0A6",
  hire: "#2EE9D3",
  consider: "#F6B44B",
  reject: "#FF3B6B",
};

export function SmartInterviewerPanel() {
  const [analysis, setAnalysis] = useState<SmartInterviewerResponse | null>(null);
  const [assistant, setAssistant] = useState<SmartInterviewAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Show top candidate.");
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUntil.current = 0;
    try {
      const payload = await fetchJson<SmartInterviewerResponse>("/api/interviews/smart/default");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("AI Smart Interviewer could not load the active panel.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runPanel = useCallback(async () => {
    setRunning(true);
    setError("");
    manualUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<SmartInterviewerResponse>("/api/interviews/smart/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(interviewStressPayload()),
      });
      setAnalysis(payload);
    } catch {
      setError("AI Smart Interviewer could not score the candidate panel.");
    } finally {
      setRunning(false);
    }
  }, []);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson<SmartInterviewAssistantResponse>("/api/interviews/smart/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      setAssistant(payload);
    } catch {
      setAssistant({
        model: "AI Smart Interview Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "error",
        answer: "AI Smart Interview Assistant could not query the interview panel.",
        confidence: 0,
        candidateIds: [],
        citedEvidence: [],
        reportArtifacts: [],
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
      try {
        const response = await fetch("/api/interviews/smart/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing Smart Interviewer stream");
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
            if (dataLine && Date.now() > manualUntil.current) {
              setAnalysis(JSON.parse(dataLine.slice(6)) as SmartInterviewerResponse);
              setLoading(false);
            }
          }
        }
        setStreamStatus("ready");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("fallback");
      }
    }

    const refreshTimer = window.setTimeout(() => {
      void loadDefault();
    }, 250);
    const streamTimer = window.setTimeout(() => {
      void connectStream();
    }, 10500);
    return () => {
      controller.abort();
      window.clearTimeout(refreshTimer);
      window.clearTimeout(streamTimer);
    };
  }, [loadDefault]);

  const rankingChart = useMemo(
    () =>
      analysis?.candidateRankings.map((candidate) => ({
        name: shortName(candidate.candidateName),
        overall: Math.round(candidate.overallScore),
        technical: Math.round(candidate.technicalScore),
        integrity: Math.round(100 - candidate.cheatingRiskScore),
      })) ?? [],
    [analysis],
  );

  const topCandidate = analysis?.candidateRankings[0] ?? null;

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <UserCheck className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Smart Interviewer</p>
            <h2 className="text-xl font-semibold text-white">Autonomous technical panel, behavioral scoring, voice confidence, cheating detection, and reports</h2>
            <p className="mt-1 max-w-4xl text-sm leading-6 text-slate-400">
              Dynamic interview questions and answer scoring are fused with resume intelligence, Smart Hiring ranker evidence, voice signals, monitoring events, and PDF/DOCX report generation.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh panel
          </button>
          <button onClick={() => void runPanel()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {running ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Run interview
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? (
        <p className="mt-5 text-sm text-slate-400">Loading interview engine, question generator, voice confidence model, and report artifacts...</p>
      ) : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Active interviews" value={String(analysis.summary.activeInterviews)} />
            <Stat label="Avg score" value={`${Math.round(analysis.summary.averageOverallScore)}%`} />
            <Stat label="Top candidate" value={shortName(analysis.summary.topCandidate)} />
            <Stat label="Strong hires" value={String(analysis.summary.strongHireCount)} />
            <Stat label="Decision briefs" value={String(analysis.summary.reportCount)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Sparkles className="size-4" />
                Candidate ranking engine
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={rankingChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Bar dataKey="overall" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="technical" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="integrity" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 grid gap-2 md:grid-cols-2 xl:grid-cols-4">
                {analysis.candidateRankings.map((candidate) => (
                  <CandidateCard key={candidate.candidateId} candidate={candidate} />
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Mic2 className="size-4" />
                Interview panel verdict
              </div>
              {topCandidate ? (
                <>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Signal label="Technical" value={topCandidate.technicalScore} color="#2EE9D3" />
                    <Signal label="Behavioral" value={topCandidate.behavioralScore} color="#7CF0A6" />
                    <Signal label="Voice confidence" value={topCandidate.voiceConfidenceScore} color="#F6B44B" />
                    <Signal label="Cheating risk" value={topCandidate.cheatingRiskScore} color="#FF3B6B" />
                  </div>
                  <div className="mt-4 border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2 text-xs uppercase">
                      <span className="text-slate-500">Recommendation</span>
                      <span style={{ color: decisionColor[topCandidate.recommendation.decision] }}>
                        {labelize(topCandidate.recommendation.decision)}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{topCandidate.recommendation.rationale}</p>
                  </div>
                  <div className="mt-4 grid gap-2">
                    {topCandidate.skillScores.slice(0, 6).map((skill) => (
                      <div key={skill.skill} className="flex items-center justify-between gap-3 border border-line/60 bg-panel/60 px-3 py-2">
                        <span className="text-xs text-slate-400">{skill.skill}</span>
                        <strong className="text-sm text-white">{Math.round(skill.score)}%</strong>
                      </div>
                    ))}
                  </div>
                </>
              ) : null}
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Integrity and risk indicators
              </div>
              <div className="grid gap-3">
                {analysis.candidateRankings.map((candidate) => (
                  <div key={`${candidate.candidateId}-risk`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <h3 className="text-sm font-medium text-white">{candidate.candidateName}</h3>
                      <span className="text-xs uppercase" style={{ color: riskColor[candidate.cheatingReport.riskLevel] }}>
                        {candidate.cheatingReport.riskLevel}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-400">{candidate.cheatingReport.recommendation}</p>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                      <RiskPill label="Copy paste" value={candidate.cheatingReport.copyPasteEvents} />
                      <RiskPill label="Tab switch" value={candidate.cheatingReport.tabSwitchEvents} />
                      <RiskPill label="External" value={candidate.cheatingReport.externalAssistanceSignals} />
                    </div>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <FileText className="size-4" />
                Questions and reports
              </div>
              <div className="grid gap-2">
                {analysis.generatedQuestions.slice(0, 5).map((item) => (
                  <div key={item.questionId} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-xs uppercase text-cyan">{labelize(item.interviewType)}</span>
                      <span className="text-xs text-slate-500">{item.difficulty}</span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{item.question}</p>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {analysis.candidateRankings.slice(0, 4).map((candidate) => (
                  <div key={`${candidate.candidateId}-report`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="text-sm font-medium text-white">{candidate.report.title}</div>
                    <p className="mt-1 text-xs text-slate-500">PDF and DOCX generated under backend interview reports.</p>
                    <p className="mt-2 truncate text-xs text-cyan">{candidate.report.pdfPath}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <article className="mt-4 border border-line/70 bg-panel2/65 p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-xs uppercase text-mint">
                <Bot className="size-4" />
                AI interview assistant
              </div>
              <div className="flex min-w-0 flex-1 justify-end gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-panel px-3 py-2 text-sm text-white outline-none focus:border-cyan md:max-w-xl"
                  aria-label="Smart Interviewer question"
                />
                <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-sm text-mint">
                  {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">
              {assistant?.answer ?? "Ask for a top candidate, candidate comparison, report generation, or an interview start sequence."}
            </p>
            {assistant?.citedEvidence.length ? (
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {assistant.citedEvidence.slice(0, 4).map((item) => (
                  <div key={item} className="border border-line/60 bg-panel/60 p-2 text-xs leading-5 text-slate-400">
                    {item}
                  </div>
                ))}
              </div>
            ) : null}
          </article>
        </>
      ) : null}
    </section>
  );
}

function CandidateCard({ candidate }: { candidate: CandidateInterviewRanking }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-2">
        <h3 className="truncate text-sm font-medium text-white">{candidate.rank}. {candidate.candidateName}</h3>
        <span className="text-xs" style={{ color: decisionColor[candidate.recommendation.decision] }}>
          {labelize(candidate.recommendation.decision)}
        </span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <Mini label="Overall" value={`${Math.round(candidate.overallScore)}%`} />
        <Mini label="Integrity" value={`${Math.round(100 - candidate.cheatingRiskScore)}%`} />
        <Mini label="Voice" value={`${Math.round(candidate.voiceConfidenceScore)}%`} />
        <Mini label="Skills" value={`${Math.round(candidate.skillMatchScore)}%`} />
      </div>
    </div>
  );
}

function Signal({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-center justify-between gap-2 text-xs uppercase text-slate-500">
        <span>{label}</span>
        <span style={{ color }}>{Math.round(value)}%</span>
      </div>
      <div className="mt-2 h-2 bg-void">
        <div className="h-full" style={{ width: `${Math.max(4, Math.min(100, value))}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-2 block truncate text-lg font-semibold text-white">{value}</strong>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/50 bg-void/30 px-2 py-1">
      <span className="block text-slate-500">{label}</span>
      <strong className="text-white">{value}</strong>
    </div>
  );
}

function RiskPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-line/50 bg-void/30 px-2 py-1">
      <span className="block text-slate-500">{label}</span>
      <strong className="text-white">{value}</strong>
    </div>
  );
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { ...init, cache: "no-store" });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return (await response.json()) as T;
}

function labelize(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function shortName(value: string) {
  const parts = value.split(" ");
  return parts.length > 1 ? `${parts[0]} ${parts[1][0]}.` : value;
}

function interviewStressPayload() {
  return {
    realtime: true,
    interview_types: ["technical", "behavioral", "system_design", "coding", "cloud", "database", "cybersecurity"],
    role: {
      role_id: "role-ai-platform-interview",
      title: "Senior AI Platform Engineer",
      job_description:
        "Build secure Python FastAPI services, Kubernetes automation, PostgreSQL and Redis reliability, MLOps model serving, API observability, and incident response.",
      required_skills: ["python", "kubernetes", "api reliability", "security", "postgresql"],
      preferred_skills: ["redis", "mlops", "incident response", "microservices", "testing"],
      seniority: "senior",
      team_context: "Enterprise AI platform team operating realtime analytics and model-serving APIs.",
      culture_values: ["ownership", "clear communication", "collaboration", "incident discipline"],
      domain_keywords: ["enterprise ai", "platform reliability", "secure api", "model serving"],
    },
    candidates: [
      {
        candidate_id: "cand-panel-elite",
        candidate_name: "Mira Chen",
        current_title: "Senior Platform Engineer",
        years_experience: 9,
        expected_salary: 186000,
        declared_skills: ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "Redis", "Security", "MLOps"],
        certifications: ["CKA", "AWS Solutions Architect"],
        resume_text:
          "Led Python FastAPI model-serving APIs, Kubernetes canary deployment, PostgreSQL tuning, Redis cache optimization, security reviews, observability, and incident postmortems. Reduced p95 latency by 39%.",
        interview_transcript:
          "I clarify customer impact, communicate tradeoffs, delegate investigation, document rollback decisions, and lead blameless postmortems.",
        portfolio_summary: "Secure MLOps gateway with tracing, rate limits, canaries, model monitoring, and rollback automation.",
        answers: [
          {
            question_id: "q-system",
            question: "Design a reliable API gateway.",
            interview_type: "system_design",
            difficulty: "senior",
            answer:
              "I would use load balancing, rate limits, JWT validation, Redis caching, Postgres read replicas, tracing, SLO metrics, circuit breakers, canary deployment, rollback, test gates, and incident runbooks.",
            response_time_seconds: 244,
          },
          {
            question_id: "q-behavior",
            question: "Describe incident ownership.",
            interview_type: "behavioral",
            difficulty: "senior",
            answer:
              "I led coordination, communicated customer impact, paired with teammates, protected psychological safety, and assigned follow-up owners after a postmortem.",
            response_time_seconds: 136,
          },
        ],
        voice_metrics: {
          words_per_minute: 136,
          hesitation_count: 2,
          pitch_variance: 0.23,
          pause_ratio: 0.1,
          volume_stability: 0.84,
        },
        monitoring_events: [],
      },
      {
        candidate_id: "cand-panel-risk",
        candidate_name: "Dax Overclaim",
        current_title: "Principal Everything Architect",
        years_experience: 3,
        expected_salary: 260000,
        declared_skills: ["Python", "Kubernetes", "Security", "MLOps", "Leadership"],
        certifications: ["Self certified cloud expert"],
        resume_text:
          "Personally owned every architecture decision for dozens of unicorn-scale platforms and mastered all cloud, AI, Kubernetes, databases, security, frontend, backend, and leadership functions. 20 years Kubernetes experience.",
        interview_transcript: "I prefer to work alone and do not need reviews or postmortems because I already know the answer.",
        portfolio_summary: "No public projects available.",
        answers: [
          {
            question_id: "q-system",
            question: "Design a reliable API gateway.",
            interview_type: "system_design",
            difficulty: "senior",
            answer: "I have mastered all cloud and architecture. Use everything perfectly. Reviews are unnecessary.",
            response_time_seconds: 11,
          },
        ],
        voice_metrics: {
          words_per_minute: 246,
          hesitation_count: 0,
          pitch_variance: 0.68,
          pause_ratio: 0.02,
          volume_stability: 0.41,
        },
        monitoring_events: [
          { event_type: "copy_paste", timestamp_offset_seconds: 18, severity_weight: 0.82, details: "Large pasted answer appeared instantly." },
          { event_type: "suspicious_speed", timestamp_offset_seconds: 21, severity_weight: 0.75, details: "Answer speed exceeded realistic response threshold." },
          { event_type: "external_assistance", timestamp_offset_seconds: 43, severity_weight: 0.7, details: "Focus left interview tab during security answer." },
        ],
      },
    ],
  };
}
