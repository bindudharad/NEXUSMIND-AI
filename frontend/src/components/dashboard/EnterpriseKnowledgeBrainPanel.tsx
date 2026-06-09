"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type React from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import {
  BookOpenCheck,
  Bot,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileSearch,
  GitBranch,
  History,
  Loader2,
  Network,
  Radio,
  RefreshCw,
  Search,
  Send,
  ShieldCheck,
  UploadCloud,
  UserRound,
} from "lucide-react";

import type {
  EnterpriseKnowledgeAskResponse,
  EnterpriseKnowledgeDefaultResponse,
  EnterpriseKnowledgeExpertRanking,
  EnterpriseKnowledgeRecommendation,
  EnterpriseKnowledgeSearchResponse,
  EnterpriseKnowledgeSummary,
} from "@/types/enterprise-knowledge";

export function EnterpriseKnowledgeBrainPanel() {
  const [brain, setBrain] = useState<EnterpriseKnowledgeDefaultResponse | null>(null);
  const [searchResult, setSearchResult] = useState<EnterpriseKnowledgeSearchResponse | null>(null);
  const [answer, setAnswer] = useState<EnterpriseKnowledgeAskResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState("Kubernetes outage node recovery strategy");
  const [question, setQuestion] = useState("Who knows Kubernetes best?");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState("");
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await fetchJson("/api/knowledge/brain/default");
      if (!isBrain(payload)) throw new Error("Malformed Company Brain payload");
      setBrain(payload);
    } catch {
      setError("Company Brain could not load enterprise knowledge memory.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runSearch = useCallback(async () => {
    setWorking("search");
    setError("");
    try {
      const payload = await fetchJson("/api/knowledge/brain/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      });
      if (!isSearch(payload)) throw new Error("Malformed search payload");
      setSearchResult(payload);
    } catch {
      setError("Semantic knowledge search failed.");
    } finally {
      setWorking("");
    }
  }, [searchQuery]);

  const askBrain = useCallback(async () => {
    setWorking("ask");
    setError("");
    try {
      const payload = await fetchJson("/api/knowledge/brain/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, top_k: 6, session_id: "dashboard" }),
      });
      if (!isAnswer(payload)) throw new Error("Malformed answer payload");
      setAnswer(payload);
    } catch {
      setError("Company Brain Q&A failed.");
    } finally {
      setWorking("");
    }
  }, [question]);

  const ingestDemo = useCallback(async () => {
    setWorking("ingest");
    setError("");
    try {
      await fetchJson("/api/knowledge/brain/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_system: "dashboard_upload",
          documents: [
            {
              document_id: "dashboard-qdrant-runbook",
              title: "Qdrant Vector Search Recovery Runbook",
              source_type: "sop",
              file_name: "qdrant-vector-search-recovery.txt",
              content:
                "Asha restored Qdrant vector search after an indexing incident by rebuilding the collection, replaying embedding jobs, validating semantic search recall, and documenting the vector recovery SOP.",
              metadata: {
                employee_id: "emp-asha",
                employee_name: "Asha",
                department: "AI Platform",
                team: "Knowledge Intelligence",
                systems: ["Qdrant", "RAG Assistant"],
                skills: ["qdrant", "vector search", "embeddings", "incident response"],
              },
            },
          ],
        }),
      });
      await loadDefault();
    } catch {
      setError("Demo document ingestion failed.");
    } finally {
      setWorking("");
    }
  }, [loadDefault]);

  const uploadSelectedFile = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;
      setWorking("upload");
      setError("");
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("title", file.name.replace(/\.[^.]+$/, "").replace(/[-_]/g, " "));
        formData.append("metadata", JSON.stringify({ source: "dashboard_file_upload" }));
        await fetchJson("/api/knowledge/brain/upload", {
          method: "POST",
          body: formData,
        });
        await loadDefault();
      } catch {
        setError("Company Brain file upload failed.");
      } finally {
        setWorking("");
        event.target.value = "";
      }
    },
    [loadDefault],
  );

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/knowledge/brain/stream", { cache: "no-store", signal: controller.signal });
        if (!response.ok) throw new Error("Company Brain stream failed");
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing stream body");
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
            if (!dataLine) continue;
            const payload = JSON.parse(dataLine.slice(6));
            if (isStreamPayload(payload)) {
              setBrain((current) =>
                current
                  ? {
                      ...current,
                      summary: payload.summary,
                      topExperts: payload.topExperts ?? current.topExperts,
                      recommendations: payload.recommendations ?? current.recommendations,
                    }
                  : current,
              );
            }
          }
        }
        setStreamStatus("polling");
      } catch {
        if (!controller.signal.aborted) setStreamStatus("polling");
      }
    }

    const initialLoad = window.setTimeout(() => {
      void loadDefault();
    }, 0);
    const streamTimer = window.setTimeout(() => {
      void connectStream();
    }, 2200);
    return () => {
      controller.abort();
      window.clearTimeout(initialLoad);
      window.clearTimeout(streamTimer);
    };
  }, [loadDefault]);

  const expertChart = useMemo(
    () =>
      brain?.topExperts.slice(0, 7).map((expert) => ({
        name: shortName(expert.employeeName),
        score: Math.round(expert.score),
        skill: expert.skill,
      })) ?? [],
    [brain],
  );

  const technologyChart = useMemo(
    () =>
      brain?.technologyMap.slice(0, 7).map((item) => ({
        name: item.title.length > 14 ? `${item.title.slice(0, 14)}...` : item.title,
        score: Math.round(item.score),
      })) ?? [],
    [brain],
  );

  const nodeTypes = useMemo(() => {
    const counts = new Map<string, number>();
    brain?.graphNodes.forEach((node) => counts.set(node.type, (counts.get(node.type) ?? 0) + 1));
    return Array.from(counts.entries()).map(([type, count]) => ({ type, count }));
  }, [brain]);

  return (
    <section data-testid="enterprise-knowledge-brain-panel" className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <BrainCircuit className="mt-1 size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Enterprise Knowledge AI / Company Brain</p>
            <h2 className="text-xl font-semibold text-white">Document ingestion, semantic memory, RAG answers, and expertise graph intelligence</h2>
            <p className="mt-2 max-w-5xl text-sm leading-6 text-slate-500">
              Preserves incident solutions, architecture decisions, expert ownership, SOP gaps, and organizational memory with cited retrieval and graph evidence.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadDefault()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Refresh
          </button>
          <input ref={fileInputRef} type="file" className="hidden" onChange={(event) => void uploadSelectedFile(event)} />
          <button onClick={() => fileInputRef.current?.click()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {working === "upload" ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}
            Upload file
          </button>
          <button onClick={() => void ingestDemo()} className="inline-flex items-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-sm text-mint">
            {working === "ingest" ? <Loader2 className="size-4 animate-spin" /> : <UploadCloud className="size-4" />}
            Ingest runbook
          </button>
        </div>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading && !brain ? <p className="mt-5 text-sm text-slate-400">Indexing enterprise memory, graph relationships, expert evidence, and retrieval citations...</p> : null}

      {brain ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-4 xl:grid-cols-9">
            <Stat label="Health" value={`${Math.round(brain.summary.knowledgeHealthScore)}%`} />
            <Stat label="Docs" value={String(brain.summary.documentsIndexed)} />
            <Stat label="Chunks" value={String(brain.summary.chunksIndexed)} />
            <Stat label="Experts" value={String(brain.summary.expertsDetected)} />
            <Stat label="Graph Nodes" value={String(brain.summary.graphNodes)} />
            <Stat label="Graph Edges" value={String(brain.summary.graphEdges)} />
            <Stat label="Incidents" value={String(brain.summary.incidentsDetected)} />
            <Stat label="Solutions" value={String(brain.summary.solutionsDetected)} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
            <StatusMetric label="Ingestion" value={brain.statusReport.knowledgeIngestionStatus} />
            <StatusMetric label="Vector DB" value={brain.statusReport.vectorDatabaseStatus} />
            <StatusMetric label="Graph" value={brain.statusReport.knowledgeGraphStatus} />
            <StatusMetric label="RAG" value={brain.statusReport.ragStatus} />
            <StatusMetric label="Security" value={brain.statusReport.securityStatus} />
            <StatusMetric label="Readiness" value={`${Math.round(brain.statusReport.productionReadinessScore)}%`} />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Search} label="Semantic search" />
              <div className="mt-3 flex gap-2">
                <input
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none"
                />
                <button onClick={() => void runSearch()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
                  {working === "search" ? <Loader2 className="size-4 animate-spin" /> : <FileSearch className="size-4" />}
                  Search
                </button>
              </div>
              <div className="mt-4 grid gap-2">
                {(searchResult?.results ?? brain.valuableDocuments.slice(0, 3)).slice(0, 4).map((item) => {
                  const title = "title" in item ? item.title : "Knowledge result";
                  const detail = "matchedChunks" in item ? item.matchedChunks[0]?.text : item.detail;
                  const score = "score" in item ? item.score : 0;
                  return <ResultRow key={`${title}-${score}`} title={title} detail={detail ?? ""} score={score} />;
                })}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Send} label="AI question answering" />
              <div className="mt-3 flex gap-2">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  className="min-w-0 flex-1 border border-line bg-void px-3 py-2 text-sm text-white outline-none"
                />
                <button onClick={() => void askBrain()} className="inline-flex items-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-sm text-mint">
                  {working === "ask" ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                  Ask
                </button>
              </div>
              <div className="mt-4 min-h-36 border border-line/70 bg-void/50 p-4">
                <p className="text-sm leading-6 text-slate-300">
                  {answer?.answer ?? "Ask about experts, incidents, architecture decisions, previous outage solutions, or project memory."}
                </p>
                {answer ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {answer.citations.slice(0, 4).map((citation) => (
                      <span key={citation.citationId} className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-xs text-cyan">
                        {citation.citationId} {citation.title}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <ChartCard icon={UserRound} label="Top experts" data={expertChart} dataKey="score" />
            <ChartCard icon={Database} label="Technology map" data={technologyChart} dataKey="score" />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Network} label="Knowledge graph" />
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {nodeTypes.map((item) => (
                  <div key={item.type} className="border border-line/60 bg-void/45 p-3">
                    <span className="text-xs uppercase text-slate-500">{item.type}</span>
                    <strong className="mt-1 block text-xl text-white">{item.count}</strong>
                  </div>
                ))}
              </div>
              <div className="mt-3 grid gap-2">
                {brain.graphEdges.slice(0, 5).map((edge) => (
                  <div key={`${edge.source}-${edge.target}-${edge.type}`} className="border border-line/60 bg-panel/55 p-3 text-xs text-slate-400">
                    <span className="text-cyan">{edge.type}</span> {edge.evidence}
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BookOpenCheck} label="Organizational memory" />
              <div className="mt-3 grid gap-3">
                {brain.incidentMemory.slice(0, 4).map((item) => (
                  <InsightRow key={item.title} title={item.title} detail={item.detail} score={item.score} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={History} label="Organizational memory timeline" />
              <div className="mt-3 grid gap-2">
                {brain.organizationalMemoryTimeline.slice(0, 6).map((event) => (
                  <div key={event.eventId} className="border border-line/60 bg-void/45 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <strong className="text-sm text-white">{event.title}</strong>
                      <span className="text-xs uppercase text-cyan">{event.eventType}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{event.summary}</p>
                    <p className="mt-2 text-xs text-slate-600">{new Date(event.occurredAt).toLocaleDateString()} · {event.people.slice(0, 3).join(", ") || "Company memory"}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={CheckCircle2} label="Lessons learned engine" />
              <div className="mt-3 grid gap-2">
                {brain.lessonsLearned.slice(0, 6).map((lesson, index) => (
                  <InsightRow key={`${lesson.title}-${lesson.detail}-${index}`} title={lesson.title} detail={lesson.detail} score={lesson.score} />
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <ListCard icon={GitBranch} label="SOP gaps" items={brain.sopGaps.map((item) => ({ title: item.title, detail: item.detail, score: item.score }))} />
            <ListCard icon={BookOpenCheck} label="Valuable documents" items={brain.valuableDocuments.map((item) => ({ title: item.title, detail: item.detail, score: item.score }))} />
            <ListCard
              icon={Radio}
              label="Knowledge-transfer recommendations"
              items={brain.recommendations.map((item) => ({ title: item.title, detail: item.action, score: item.expectedImpact }))}
            />
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-3">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={ShieldCheck} label="Security and access control" />
              <div className="mt-3 grid gap-2">
                {brain.securityControls.map((control) => (
                  <div key={control.control} className="border border-line/60 bg-void/45 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <strong className="text-sm text-white">{control.control}</strong>
                      <span className="text-xs uppercase text-mint">{control.status}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{control.detail}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={BrainCircuit} label="Digital twin integration" />
              <div className="mt-3 grid gap-2">
                {brain.digitalTwinSync.map((sync) => (
                  <div key={sync.system} className="border border-line/60 bg-void/45 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <strong className="text-sm text-white">{sync.system}</strong>
                      <span className="text-xs uppercase text-cyan">{sync.status}</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{sync.update}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <PanelTitle icon={Bot} label="Knowledge intelligence council" />
              <div className="mt-3 grid gap-2">
                {brain.agentCouncil.map((agent) => (
                  <div key={agent.agent} className="border border-line/60 bg-void/45 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <strong className="text-sm text-white">{agent.agent}</strong>
                      <span className="text-xs text-cyan">{Math.round(agent.confidence * 100)}%</span>
                    </div>
                    <p className="mt-1 text-xs leading-5 text-slate-500">{agent.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <InfraStatus label="Qdrant" value={brain.summary.qdrantStatus} />
            <InfraStatus label="Neo4j" value={brain.summary.neo4jStatus} />
          </div>

          <div className="mt-4 border border-mint/30 bg-mint/10 p-3 text-sm text-mint">{brain.finalVerdict}</div>
        </>
      ) : null}
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <span className="text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-2 block text-lg text-white">{value}</strong>
    </div>
  );
}

function StatusMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 border border-cyan/20 bg-cyan/10 p-3">
      <span className="text-xs uppercase text-cyan">{label}</span>
      <strong className="mt-2 block truncate text-sm text-white">{value.replaceAll("_", " ")}</strong>
    </div>
  );
}

function PanelTitle({ icon: Icon, label }: { icon: React.ComponentType<{ className?: string }>; label: string }) {
  return (
    <div className="flex items-center gap-2 text-xs uppercase text-cyan">
      <Icon className="size-4" />
      <span>{label}</span>
    </div>
  );
}

function ChartCard({
  icon,
  label,
  data,
  dataKey,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  data: Array<Record<string, string | number>>;
  dataKey: string;
}) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <PanelTitle icon={icon} label={label} />
      <div className="mt-3 h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ left: -24, right: 8, top: 8, bottom: 0 }}>
            <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
            <XAxis dataKey="name" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
            <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
            <Bar dataKey={dataKey} fill="#2EE9D3" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </article>
  );
}

function ResultRow({ title, detail, score }: { title: string; detail: string; score: number }) {
  return (
    <div className="border border-line/60 bg-void/45 p-3">
      <div className="flex items-start justify-between gap-3">
        <strong className="text-sm text-white">{title}</strong>
        <span className="text-xs text-cyan">{Math.round(score * 100) / 100}</span>
      </div>
      <p className="mt-1 line-clamp-2 text-xs leading-5 text-slate-500">{detail}</p>
    </div>
  );
}

function InsightRow({ title, detail, score }: { title: string; detail: string; score: number }) {
  return (
    <div className="border border-line/60 bg-void/45 p-3">
      <div className="flex items-center justify-between gap-3">
        <strong className="text-sm text-white">{title}</strong>
        <span className="text-xs text-mint">{Math.round(score)}%</span>
      </div>
      <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>
    </div>
  );
}

function ListCard({
  icon,
  label,
  items,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  items: { title: string; detail: string; score: number }[];
}) {
  return (
    <article className="border border-line/70 bg-panel2/65 p-4">
      <PanelTitle icon={icon} label={label} />
      <div className="mt-3 grid gap-2">
        {items.slice(0, 5).map((item) => (
          <InsightRow key={`${label}-${item.title}`} title={item.title} detail={item.detail} score={item.score} />
        ))}
      </div>
    </article>
  );
}

function InfraStatus({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/60 bg-void/40 p-3">
      <span className="text-xs uppercase text-slate-500">{label} adapter</span>
      <p className="mt-1 text-xs text-slate-400">{value}</p>
    </div>
  );
}

async function fetchJson(input: string, init?: RequestInit) {
  const response = await fetch(input, { ...init, cache: "no-store" });
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return (await response.json()) as unknown;
}

function shortName(value: string) {
  const parts = value.split(" ").filter(Boolean);
  return parts.length > 1 ? `${parts[0]} ${parts[1][0]}.` : value;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object");
}

function isBrain(value: unknown): value is EnterpriseKnowledgeDefaultResponse {
  return isObject(value) && isObject(value.summary) && Array.isArray(value.documents) && Array.isArray(value.topExperts);
}

function isSearch(value: unknown): value is EnterpriseKnowledgeSearchResponse {
  return isObject(value) && Array.isArray(value.results) && Array.isArray(value.citations);
}

function isAnswer(value: unknown): value is EnterpriseKnowledgeAskResponse {
  return isObject(value) && typeof value.answer === "string" && Array.isArray(value.citations);
}

function isStreamPayload(
  value: unknown,
): value is {
  summary: EnterpriseKnowledgeSummary;
  topExperts?: EnterpriseKnowledgeExpertRanking[];
  recommendations?: EnterpriseKnowledgeRecommendation[];
} {
  return isObject(value) && isObject(value.summary);
}
