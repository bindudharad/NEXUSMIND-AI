"use client";

import { Bot, BrainCircuit, FileText, Loader2, Radio, Send, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { GenAIHRAssistantResponse } from "@/types/genai-hr";

const samplePrompts = [
  "Show highest-risk workforce segments.",
  "Which team has highest burnout risk?",
  "Predict next month productivity.",
  "Which projects may fail next sprint?",
  "Which department needs capacity investment urgently?",
  "Generate executive workforce intelligence brief.",
];

export function GenAIHRAssistantPanel() {
  const [analysis, setAnalysis] = useState<GenAIHRAssistantResponse | null>(null);
  const [question, setQuestion] = useState("Generate executive workforce intelligence brief.");
  const [streamText, setStreamText] = useState("");
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState("");
  const [sessionId] = useState(() => `enterprise-people-intelligence-${Date.now().toString(36)}`);

  const ask = useCallback(
    async (prompt: string, stream = false) => {
      setError("");
      setLoading(true);
      if (stream) {
        setStreaming(true);
        setStreamText("");
      }
      const payload = {
        question: prompt,
        session_id: sessionId,
        include_realtime: true,
        report_format: prompt.toLowerCase().includes("report") ? "board" : "executive",
      };
      try {
        if (!stream) {
          const response = await fetch("/api/genai/hr/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            cache: "no-store",
          });
          const data = await response.json();
          if (!response.ok || !isGenAIHRResponse(data)) throw new Error("Malformed people intelligence copilot response");
          setAnalysis(data);
          setStreamText(data.answer);
          return;
        }
        const response = await fetch("/api/genai/hr/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          cache: "no-store",
        });
        if (!response.ok || !response.body) throw new Error("People intelligence stream failed");
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";
          for (const event of events) {
            const dataLine = event.split("\n").find((line) => line.startsWith("data: "));
            if (!dataLine) continue;
            const data = JSON.parse(dataLine.slice(6));
            if (data.type === "token" && typeof data.token === "string") {
              setStreamText((current) => current + data.token);
            } else if (isGenAIHRResponse(data)) {
              setAnalysis(data);
            }
          }
        }
      } catch {
        setError("Executive people intelligence copilot could not complete the query.");
      } finally {
        setLoading(false);
        setStreaming(false);
      }
    },
    [sessionId],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void ask("Generate executive workforce intelligence brief.", false);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [ask]);

  const successfulTools = useMemo(() => analysis?.toolCalls.filter((call) => call.status === "success").length ?? 0, [analysis]);
  const topContext = analysis?.retrievedContext.slice(0, 4) ?? [];
  const answer = streamText || analysis?.answer || "";

  return (
    <section id="genai-hr-assistant" data-testid="genai-hr-assistant-panel" className="border border-cyan/25 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2 text-xs text-cyan">
            <Bot className="size-4" />
            <span>Executive People Intelligence Copilot</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">Executive workforce intelligence and RAG reasoning system</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Conversational AI interface, realtime streaming responses, executive intelligence widgets, people-risk reasoning, report-generation controls, AI recommendation panels, and context-aware conversation history.
          </p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          <Metric label="Intent" value={analysis?.intent ?? "loading"} />
          <Metric label="Confidence" value={analysis ? `${Math.round(analysis.confidence * 100)}%` : "..."} />
          <Metric label="Tool calls" value={String(successfulTools)} />
          <Metric label="Memory turns" value={String(analysis?.conversationMemory.turns ?? 0)} />
        </div>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-[1fr_auto_auto]">
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          className="min-h-24 border border-line bg-void/70 p-3 text-sm text-slate-200 outline-none focus:border-cyan/60"
          placeholder="Ask: show highest-risk workforce segments, generate an executive intelligence brief, predict next month productivity..."
        />
        <button
          type="button"
          onClick={() => void ask(question, true)}
          className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-4 py-3 text-sm text-cyan"
          data-testid="stream-genai-hr"
        >
          {streaming ? <Loader2 className="size-4 animate-spin" /> : <Radio className="size-4" />}
          Stream answer
        </button>
        <button
          type="button"
          onClick={() => void ask(question, false)}
          className="inline-flex items-center justify-center gap-2 border border-line bg-panel2 px-4 py-3 text-sm text-slate-300"
          data-testid="ask-genai-hr"
        >
          {loading && !streaming ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
          Ask
        </button>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {samplePrompts.map((prompt) => (
          <button
            key={prompt}
            type="button"
            onClick={() => {
              setQuestion(prompt);
              void ask(prompt, prompt.includes("report"));
            }}
            className="border border-line/70 bg-panel2/65 px-3 py-2 text-xs text-slate-300 hover:border-cyan/50"
          >
            {prompt}
          </button>
        ))}
        <button
          type="button"
          onClick={() => void ask("Generate executive workforce intelligence brief.", true)}
          className="inline-flex items-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-xs text-mint"
          data-testid="generate-hr-report"
        >
          <FileText className="size-3.5" />
          Generate intelligence brief
        </button>
      </div>

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
        <article className="border border-cyan/25 bg-cyan/10 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-xs uppercase text-cyan">
              <Sparkles className="size-4" />
              Realtime streaming responses
            </div>
            <span className="text-xs text-slate-500">{analysis?.model ?? "loading model"}</span>
          </div>
          <p className="mt-4 min-h-36 whitespace-pre-wrap text-sm leading-7 text-slate-200">
            {answer || "Waiting for the assistant to retrieve workforce context and generate an answer..."}
          </p>
          <p className="mt-4 border-t border-cyan/20 pt-3 text-xs leading-5 text-slate-400">{analysis?.executiveSummary ?? "Executive summary will appear after the first grounded response."}</p>
        </article>

        <article className="border border-line/70 bg-panel2/65 p-4">
          <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
            <BrainCircuit className="size-4" />
            RAG retrieval and memory
          </div>
          <div className="space-y-2">
            {topContext.map((source) => (
              <div key={source.citationId} className="border border-line/60 bg-panel/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-white">{source.citationId}. {source.title}</span>
                  <span className="text-xs text-cyan">{Math.round(source.confidence * 100)}%</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{source.snippet}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 border border-line/60 bg-void/50 p-3 text-xs leading-5 text-slate-400">
            {analysis?.conversationMemory.memorySummary ?? "Context-aware conversation history initializes after the first query."}
          </p>
        </article>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr]">
        <article className="border border-line/70 bg-panel2/65 p-4">
          <div className="mb-3 text-xs uppercase text-cyan">Agent tool execution</div>
          <div className="grid gap-2 md:grid-cols-2">
            {(analysis?.toolCalls ?? []).slice(0, 8).map((call) => (
              <div key={call.name} className="border border-line/60 bg-panel/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-white">{call.name.replaceAll("_", " ")}</span>
                  <span className={call.status === "success" ? "text-xs text-mint" : "text-xs text-signal"}>{call.status}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{call.summary}</p>
                <p className="mt-2 text-xs text-slate-500">{call.latencyMs}ms</p>
              </div>
            ))}
          </div>
        </article>

        <article className="border border-line/70 bg-panel2/65 p-4">
          <div className="mb-3 text-xs uppercase text-mint">AI recommendation panels</div>
          <div className="space-y-2">
            {(analysis?.recommendedActions ?? []).slice(0, 6).map((action) => (
              <p key={action} className="border border-line/60 bg-panel/60 p-3 text-sm leading-6 text-slate-300">
                {action}
              </p>
            ))}
          </div>
        </article>
      </div>

      <div className="mt-5 border border-line/70 bg-panel2/65 p-4">
        <div className="mb-3 text-xs uppercase text-amber">Executive query console and intelligence-brief controls</div>
        <div className="grid gap-3 xl:grid-cols-4">
          {(analysis?.reportSections ?? []).map((section) => (
            <div key={section.title} className="border border-line/60 bg-panel/60 p-3">
              <h3 className="text-sm font-semibold text-white">{section.title}</h3>
              <p className="mt-2 text-xs leading-5 text-slate-400">{section.summary}</p>
              <div className="mt-3 grid gap-1 text-xs text-slate-500">
                {Object.entries(section.metrics).slice(0, 3).map(([key, value]) => (
                  <span key={key}>{key.replaceAll("_", " ")}: {String(value)}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/70 p-3">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <strong className="mt-2 block text-sm font-semibold text-white">{value}</strong>
    </div>
  );
}

function isGenAIHRResponse(value: unknown): value is GenAIHRAssistantResponse {
  const payload = value as GenAIHRAssistantResponse;
  return Boolean(payload?.answer && payload?.conversationMemory && Array.isArray(payload?.toolCalls) && Array.isArray(payload?.retrievedContext));
}
