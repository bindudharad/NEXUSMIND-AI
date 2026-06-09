"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  Award,
  BriefcaseBusiness,
  GraduationCap,
  Handshake,
  Loader2,
  Network,
  RefreshCw,
  Search,
  Send,
  Sparkles,
  Trophy,
  UserRoundSearch,
  UsersRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type React from "react";

import type {
  TalentAssistantResponse,
  TalentMarketplaceResponse,
  TalentSearchResponse,
} from "@/types/talent-marketplace";

type RequestOptions = RequestInit & { body?: BodyInit | null };

export function TalentMarketplacePanel() {
  const [analysis, setAnalysis] = useState<TalentMarketplaceResponse | null>(null);
  const [assistant, setAssistant] = useState<TalentAssistantResponse | null>(null);
  const [searchResults, setSearchResults] = useState<TalentSearchResponse | null>(null);
  const [question, setQuestion] = useState("Who can mentor me on Kubernetes?");
  const [query, setQuery] = useState("kubernetes mlops project");
  const [loading, setLoading] = useState(true);
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUntil.current = 0;
    try {
      const payload = await fetchJson<TalentMarketplaceResponse>("/api/talent/marketplace/default");
      setAnalysis(payload);
      setStreamStatus((status) => (status === "connecting" ? "polling" : status));
    } catch {
      setError("Talent marketplace could not load.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runScenario = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<TalentMarketplaceResponse>("/api/talent/marketplace/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(marketplaceScenarioPayload()),
      });
      setAnalysis(payload);
    } catch {
      setError("Talent marketplace scenario could not run.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runSearch = useCallback(async () => {
    if (!query.trim()) return;
    setSearchLoading(true);
    try {
      const payload = await fetchJson<TalentSearchResponse>("/api/talent/marketplace/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, limit: 6 }),
      });
      setSearchResults(payload);
    } catch {
      setSearchResults({
        model: "Talent Marketplace Search",
        generatedAt: new Date().toISOString(),
        query,
        results: [],
        sourceSystems: [],
      });
    } finally {
      setSearchLoading(false);
    }
  }, [query]);

  const askAssistant = useCallback(async () => {
    if (!question.trim()) return;
    setAssistantLoading(true);
    try {
      const payload = await fetchJson<TalentAssistantResponse>("/api/talent/marketplace/assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      setAssistant(payload);
    } catch {
      setAssistant({
        model: "Talent AI Assistant",
        generatedAt: new Date().toISOString(),
        question,
        intent: "summary",
        answer: "Talent AI Assistant could not query the marketplace.",
        confidence: 0,
        citedProfiles: [],
        citedOpportunities: [],
        recommendedActions: [],
        evidence: [],
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
        const response = await fetch("/api/talent/marketplace/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing talent marketplace stream");
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
              setAnalysis(JSON.parse(dataLine.slice(6)) as TalentMarketplaceResponse);
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
    }, 300);
    const streamTimer = window.setTimeout(() => {
      void connectStream();
    }, 10000);
    return () => {
      controller.abort();
      window.clearTimeout(refreshTimer);
      window.clearTimeout(streamTimer);
    };
  }, [loadDefault]);

  const reputationChart = useMemo(
    () =>
      analysis?.reputationScores.slice(0, 6).map((item) => ({
        name: shortName(item.employeeName),
        reputation: Math.round(item.totalReputation),
        knowledge: Math.round(item.knowledgeScore),
        mentorship: Math.round(item.mentorshipScore),
      })) ?? [],
    [analysis],
  );

  const projectChart = useMemo(
    () =>
      analysis?.projectMatches.slice(0, 6).map((item) => ({
        name: shortName(item.employeeName),
        match: Math.round(item.matchScore),
        skills: Math.round(item.skillCoverage),
      })) ?? [],
    [analysis],
  );

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <Network className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">AI Internal Talent Marketplace</p>
            <h2 className="text-xl font-semibold text-white">Internal projects, mentors, jobs, learning paths, experts, reputation, and skill badges</h2>
            <p className="mt-1 max-w-4xl text-sm leading-6 text-slate-400">
              Marketplace graph matches employees to growth opportunities using skill intelligence, capacity, career goals, verified expertise, learning velocity, and contribution history.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <button onClick={() => void runScenario()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
            Run mobility scenario
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !analysis ? <p className="mt-5 text-sm text-slate-400">Loading talent profiles, skill graph, project matches, mentors, internal jobs, learning paths, and badges...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-8">
            <Stat label="Profiles" value={String(analysis.summary.profiles)} />
            <Stat label="Skills" value={String(analysis.summary.skillsDetected)} />
            <Stat label="Projects" value={String(analysis.summary.projectMatches)} />
            <Stat label="Mentors" value={String(analysis.summary.mentorMatches)} />
            <Stat label="Jobs" value={String(analysis.summary.internalRoleMatches)} />
            <Stat label="Badges" value={String(analysis.summary.badgesAwarded)} />
            <Stat label="Health" value={`${Math.round(analysis.summary.marketplaceHealthScore)}%`} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <ChartPanel title="Project matching engine" icon={BriefcaseBusiness}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={projectChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="match" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="skills" fill="#7CF0A6" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>

            <ChartPanel title="Reputation engine" icon={Trophy}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={reputationChart} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                  <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                  <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                  <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                  <Bar dataKey="reputation" fill="#F6B44B" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="knowledge" fill="#38BDF8" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="mentorship" fill="#A78BFA" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </ChartPanel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_0.95fr]">
            <Panel title="Project opportunities" icon={BriefcaseBusiness}>
              {analysis.projectMatches.slice(0, 5).map((item) => (
                <Item
                  key={`${item.employeeId}-${item.projectId}`}
                  title={`${item.employeeName} -> ${item.projectTitle}`}
                  badge={`${Math.round(item.matchScore)}%`}
                  text={`${item.rationale} Missing: ${item.missingSkills.join(", ") || "none"}.`}
                />
              ))}
            </Panel>

            <Panel title="Mentor marketplace" icon={Handshake}>
              {analysis.mentorMatches.slice(0, 5).map((item) => (
                <Item key={`${item.mentorId}-${item.menteeId}-${item.topic}`} title={`${item.mentorName} -> ${item.menteeName}`} badge={item.topic} text={item.rationale} />
              ))}
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <Panel title="Internal jobs" icon={UsersRound}>
              {analysis.internalRoleMatches.slice(0, 4).map((item) => (
                <Item key={`${item.employeeId}-${item.roleId}`} title={`${item.employeeName} -> ${item.roleTitle}`} badge={`${Math.round(item.matchScore)}%`} text={item.rationale} />
              ))}
            </Panel>

            <Panel title="Learning paths" icon={GraduationCap}>
              {analysis.learningPaths.slice(0, 4).map((item) => (
                <Item key={`${item.employeeId}-${item.resourceId}-${item.targetSkill}`} title={`${item.employeeName}: ${item.targetSkill}`} badge={`${item.estimatedWeeksToProficiency}w`} text={item.rationale} />
              ))}
            </Panel>

            <Panel title="Expert discovery" icon={UserRoundSearch}>
              {analysis.expertRankings.slice(0, 4).map((item) => (
                <Item key={`${item.skill}-${item.employeeId}`} title={`${item.employeeName} knows ${item.skill}`} badge={`${Math.round(item.score)}%`} text={item.evidence.slice(0, 2).join(" | ")} />
              ))}
            </Panel>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <Panel title="Badges and graph" icon={Award}>
              <div className="grid gap-2 sm:grid-cols-2">
                {analysis.badges.slice(0, 6).map((badge) => (
                  <div key={`${badge.employeeId}-${badge.badge}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-medium text-white">{badge.badge}</span>
                      <span className="text-xs uppercase text-mint">{badge.level}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-400">{badge.employeeName}</p>
                  </div>
                ))}
              </div>
              <div className="mt-3 border border-line/60 bg-panel/60 p-3 text-xs text-slate-400">
                Graph: {analysis.graphNodes.length} nodes, {analysis.graphEdges.length} relationships. Top expert: {analysis.summary.topExpert}. Top match: {analysis.summary.topProjectMatch}.
              </div>
            </Panel>

            <Panel title="Search and Talent AI Assistant" icon={Search}>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <div className="flex gap-2">
                    <input
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan"
                      placeholder="Search skills, projects, roles"
                    />
                    <button onClick={() => void runSearch()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                      {searchLoading ? <Loader2 className="size-4 animate-spin" /> : <Search className="size-4" />}
                    </button>
                  </div>
                  <div className="mt-3 grid gap-2">
                    {(searchResults?.results ?? []).slice(0, 4).map((item) => (
                      <Item key={`${item.entityType}-${item.entityId}`} title={item.title} badge={`${Math.round(item.score)}%`} text={item.matchedSkills.join(", ") || item.summary} />
                    ))}
                  </div>
                </div>
                <div>
                  <div className="flex gap-2">
                    <input
                      value={question}
                      onChange={(event) => setQuestion(event.target.value)}
                      className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none focus:border-cyan"
                      placeholder="Ask talent assistant"
                    />
                    <button onClick={() => void askAssistant()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                      {assistantLoading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                    </button>
                  </div>
                  {assistant ? (
                    <div className="mt-3 border border-line/60 bg-panel/60 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs uppercase text-cyan">{assistant.intent}</span>
                        <span className="text-xs text-mint">{Math.round(assistant.confidence * 100)}%</span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-slate-300">{assistant.answer}</p>
                      <p className="mt-2 text-xs leading-5 text-slate-500">{assistant.recommendedActions[0]}</p>
                    </div>
                  ) : null}
                </div>
              </div>
            </Panel>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {analysis.recommendations.slice(0, 6).map((item) => (
              <div key={`${item.category}-${item.title}`} className="border border-line/70 bg-panel2/65 p-4">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-medium text-white">{item.title}</h3>
                  <span className="text-xs uppercase text-cyan">{item.priority}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-300">{item.action}</p>
                <p className="mt-2 text-xs leading-5 text-slate-500">{item.expectedImpact}</p>
              </div>
            ))}
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

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <SectionTitle icon={Icon} label={title} />
      <div className="grid gap-3">{children}</div>
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

function Item({ title, badge, text }: { title: string; badge: string; text: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-medium text-white">{title}</h3>
        <span className="shrink-0 text-xs text-cyan">{badge}</span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-400">{text}</p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-1 truncate text-lg font-semibold text-white">{value}</p>
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

async function fetchJson<T>(url: string, init?: RequestOptions): Promise<T> {
  const response = await fetch(url, { ...init, cache: "no-store" });
  if (!response.ok) throw new Error(await response.text());
  return (await response.json()) as T;
}

function marketplaceScenarioPayload() {
  return {
    focus_skills: ["python", "kubernetes", "mlops", "rag", "security", "mentoring", "system design"],
    profiles: [
      {
        employee_id: "talent-custom-001",
        employee_name: "Priya Raman",
        role: "Senior AI Engineer",
        department: "AI Platform",
        location: "Bangalore",
        skills: ["python", "rag", "vector search", "model evaluation", "mlops"],
        experience_years: 7,
        certifications: ["ML Engineering"],
        projects: ["Payment failure RAG assistant", "Vector search evaluation", "Model serving"],
        achievements: ["Cut hallucinated support answers by 32%", "Mentored three engineers on RAG evaluation"],
        interests: ["knowledge graph", "ai platform"],
        career_goals: ["Principal AI Platform Architect"],
        learning_goals: ["kubernetes", "system design"],
        expertise_areas: ["rag", "mlops", "python"],
        offered_expertise: ["rag", "vector search", "mlops"],
        wants_mentorship: true,
        wants_projects: true,
        wants_internal_roles: true,
        capacity_hours: 40,
        allocated_hours: 24,
        performance_score: 93,
        learning_velocity: 0.9,
        mentorship_hours: 28,
        knowledge_contributions: 21,
        reputation_events: 26,
      },
      {
        employee_id: "talent-custom-002",
        employee_name: "Nikhil Shah",
        role: "Backend Engineer",
        department: "Engineering",
        location: "Pune",
        skills: ["python", "fastapi", "postgresql", "api reliability"],
        experience_years: 4,
        certifications: ["AWS Cloud Practitioner"],
        projects: ["Billing API", "Incident postmortem automation"],
        achievements: ["Improved billing API p95 latency"],
        interests: ["platform engineering", "cloud"],
        career_goals: ["Staff Backend Engineer"],
        learning_goals: ["kubernetes", "mlops"],
        expertise_areas: ["fastapi", "postgresql"],
        offered_expertise: ["fastapi"],
        wants_mentorship: true,
        wants_projects: true,
        wants_internal_roles: true,
        capacity_hours: 40,
        allocated_hours: 31,
        performance_score: 84,
        learning_velocity: 0.74,
        mentorship_hours: 2,
        knowledge_contributions: 8,
        reputation_events: 11,
      },
    ],
    projects: [
      {
        project_id: "market-custom-proj-001",
        title: "Enterprise RAG Quality Upgrade",
        department: "AI Platform",
        description: "Improve retrieval and answer quality for company brain workflows.",
        required_skills: ["python", "rag", "vector search", "mlops"],
        stretch_skills: ["kubernetes", "knowledge graph"],
        priority: 5,
        duration_weeks: 8,
        open_slots: 2,
        reputation_boost: 18,
        business_impact: 91,
      },
    ],
    internal_roles: [
      {
        role_id: "market-custom-role-001",
        title: "Principal AI Platform Architect",
        department: "AI Platform",
        level: "Principal",
        required_skills: ["python", "rag", "mlops", "system design"],
        preferred_skills: ["kubernetes", "vector search"],
        career_track: "technical_leadership",
        growth_score: 94,
        vacancy_urgency: 72,
      },
    ],
  };
}
