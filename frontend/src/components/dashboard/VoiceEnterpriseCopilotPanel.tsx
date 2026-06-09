"use client";

import { Brain, CheckCircle2, Crown, History, Maximize2, Mic, MicOff, Minimize2, PlayCircle, Radio, Send, Shield, Volume2, Workflow, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import type { VoiceCommandResponse, VoiceTTSMetadata } from "@/types/voice";

type BrowserSpeechRecognitionEvent = Event & {
  results: {
    length: number;
    [index: number]: {
      isFinal: boolean;
      [index: number]: { transcript: string };
    };
  };
};

type BrowserSpeechRecognition = EventTarget & {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onerror: ((event: Event) => void) | null;
  onresult: ((event: BrowserSpeechRecognitionEvent) => void) | null;
};

type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

type SpeechWindow = Window &
  typeof globalThis & {
    SpeechRecognition?: BrowserSpeechRecognitionConstructor;
    webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
  };

const EXECUTIVE_COMMANDS = [
  "Show biggest company threat.",
  "Which department may fail next month?",
  "Show biggest company risk.",
  "Predict next quarter.",
  "What should management focus on?",
  "What happens if 30 engineers resign?",
  "Show highest-risk department.",
  "Predict next quarter revenue.",
  "How did we solve this before?",
  "Show cybersecurity threats.",
  "Show top project risks.",
  "Where should management focus?",
];

const SESSION_ID = `jarvis-ceo-${Math.random().toString(36).slice(2, 10)}`;
const CEO_DEMO_COMMAND = "Show biggest company threat.";
const CEO_DEMO_STEPS = [
  "AI listens to the CEO",
  "Company state loads",
  "Risk heatmap updates",
  "Forecast charts animate",
  "Digital twins synchronize",
  "AI Agent Council debates",
  "Spoken recommendation returns",
];
const JUDGE_IMPACT_STAGES = [
  ["Risk Heatmap", "Department risk map turns live and highlights the failing operating zone."],
  ["Burnout Visualization", "Burnout pressure recalculates from workforce and delivery signals."],
  ["Digital Twin Update", "Employee, team, department, project, and company twins synchronize."],
  ["Forecast Charts", "30-day, 90-day, revenue, workforce, and risk forecasts animate."],
  ["Agent Council", "AI managers collaborate and produce a unified executive view."],
  ["Recovery Plan", "Immediate, short-term, long-term, and risk-reduction actions appear."],
  ["Shadow Company", "Current Company -> Future Company -> Predicted Outcome is visualized."],
];

export function VoiceEnterpriseCopilotPanel() {
  const [command, setCommand] = useState(CEO_DEMO_COMMAND);
  const [liveTranscript, setLiveTranscript] = useState("");
  const [current, setCurrent] = useState<VoiceCommandResponse | null>(null);
  const [history, setHistory] = useState<VoiceCommandResponse[]>([]);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [jarvisMode, setJarvisMode] = useState(false);
  const [ceoDemoRunning, setCeoDemoRunning] = useState(false);
  const [ceoDemoStep, setCeoDemoStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const streamReceivedRef = useRef(false);
  const demoTimerRef = useRef<number | null>(null);
  const demoFinishTimerRef = useRef<number | null>(null);
  const requestSequenceRef = useRef(0);

  const sourceSystems = useMemo(() => current?.sourceSystems.slice(0, 7) ?? [], [current]);
  const isJudgeDemoResult = current?.recognizedIntent === "department_failure_forecast" || current?.recognizedIntent === "company_threat";

  useEffect(() => {
    const eventSource = new EventSource("/api/voice/copilot/stream");
    eventSource.addEventListener("voice_copilot", () => {
      streamReceivedRef.current = true;
      setStreamStatus("live");
    });
    eventSource.onerror = () => setStreamStatus(streamReceivedRef.current ? "live" : "degraded");
    return () => eventSource.close();
  }, []);

  useEffect(() => {
    return () => {
      if (demoTimerRef.current) window.clearInterval(demoTimerRef.current);
      if (demoFinishTimerRef.current) window.clearTimeout(demoFinishTimerRef.current);
    };
  }, []);

  async function executeCommand(nextCommand = command, shouldSpeak = true): Promise<VoiceCommandResponse | null> {
    const trimmed = nextCommand.trim();
    if (!trimmed) return null;
    const requestId = requestSequenceRef.current + 1;
    requestSequenceRef.current = requestId;
    setError(null);
    setCommand(trimmed);
    setLiveTranscript(trimmed);
    try {
      const response = await fetch("/api/voice/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript: trimmed,
          speaker: "CEO",
          department: "Executive",
          include_spoken_response: true,
          session_id: SESSION_ID,
          context_turns: history.slice(-4).map((item) => item.transcript),
        }),
      });
      if (!response.ok) throw new Error("Voice command failed");
      const payload = (await response.json()) as VoiceCommandResponse;
      if (requestId !== requestSequenceRef.current) return payload;
      setCurrent(payload);
      setHistory((items) => [payload, ...items].slice(0, 6));
      if (shouldSpeak) speakResponse(payload.spokenResponse || payload.answer, payload.tts);
      return payload;
    } catch {
      setError("Voice command execution failed.");
      return null;
    }
  }

  async function runCeoDemo() {
    if (demoTimerRef.current) window.clearInterval(demoTimerRef.current);
    if (demoFinishTimerRef.current) window.clearTimeout(demoFinishTimerRef.current);
    setCeoDemoRunning(true);
    setCeoDemoStep(0);
    demoTimerRef.current = window.setInterval(() => {
      setCeoDemoStep((step) => Math.min(CEO_DEMO_STEPS.length - 1, step + 1));
    }, 950);
    demoFinishTimerRef.current = window.setTimeout(() => {
      setCeoDemoStep(CEO_DEMO_STEPS.length - 1);
      setCeoDemoRunning(false);
    }, 12000);
    const response = await executeCommand(CEO_DEMO_COMMAND, true);
    if (demoTimerRef.current) window.clearInterval(demoTimerRef.current);
    if (demoFinishTimerRef.current) window.clearTimeout(demoFinishTimerRef.current);
    setCeoDemoStep(CEO_DEMO_STEPS.length - 1);
    setCeoDemoRunning(false);
    if (response?.dashboardControl?.panelId) {
      document.getElementById("voice-enterprise-copilot-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function startListening() {
    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setError(null);
      setLiveTranscript(CEO_DEMO_COMMAND);
      void runCeoDemo();
      return;
    }
    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => {
      setIsListening(false);
      setError("Microphone transcription stopped. Use typed command mode if permission is blocked.");
    };
    recognition.onresult = (event) => {
      let transcript = "";
      for (let index = 0; index < event.results.length; index += 1) {
        transcript += event.results[index][0]?.transcript ?? "";
      }
      const cleaned = transcript.trim();
      setLiveTranscript(cleaned);
      setCommand(cleaned);
      const last = event.results[event.results.length - 1];
      if (last?.isFinal && cleaned) {
        recognition.stop();
        void executeCommand(cleaned);
      }
    };
    recognitionRef.current = recognition;
    recognition.start();
  }

  function stopListening() {
    recognitionRef.current?.stop();
    setIsListening(false);
  }

  function speakResponse(text: string, tts?: VoiceTTSMetadata) {
    if (!("speechSynthesis" in window) || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = tts?.rate ?? 0.94;
    utterance.pitch = tts?.pitch ?? 1;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }

  function controlDashboard() {
    const panelId = current?.dashboardControl.panelId;
    if (!panelId) return;
    document.getElementById(panelId)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <section
      id="voice-enterprise-copilot-panel"
      data-testid="voice-enterprise-copilot-panel"
      className={`border border-cyan/25 bg-panel/85 p-4 shadow-control ${jarvisMode ? "fixed inset-4 z-50 overflow-auto bg-slate-950/95" : ""}`}
    >
      <div className="flex flex-col gap-3 border-b border-line pb-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Radio className="h-4 w-4" />
            <span>Voice-Controlled Enterprise AI</span>
            <span className="rounded border border-cyan/30 px-2 py-1 text-[10px] text-cyan">{streamStatus}</span>
          </div>
          <h2 className="mt-2 text-2xl font-semibold text-white">JARVIS for CEOs</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
            Speak or type executive commands. Responses are grounded in live company health, boardroom risk, security, revenue forecasting, clients, projects, and digital twin simulations.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setJarvisMode((enabled) => !enabled)}
            className="inline-flex h-10 items-center gap-2 border border-mint/40 bg-mint/10 px-3 text-sm font-semibold text-mint"
            title={jarvisMode ? "Exit JARVIS mode" : "Open JARVIS mode"}
          >
            {jarvisMode ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            {jarvisMode ? "Exit JARVIS" : "JARVIS Mode"}
          </button>
          <button
            type="button"
            onClick={isListening ? stopListening : startListening}
            className={`inline-flex h-10 items-center gap-2 border px-3 text-sm font-semibold transition ${
              isListening ? "border-red-400 bg-red-500/15 text-red-100" : "border-cyan/40 bg-cyan/10 text-cyan"
            }`}
            title={isListening ? "Stop microphone" : "Start microphone"}
          >
            {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            {isListening ? "Listening" : "Mic"}
          </button>
          <button
            type="button"
            onClick={() => current && speakResponse(current.spokenResponse || current.answer, current.tts)}
            className="inline-flex h-10 items-center gap-2 border border-line bg-white/5 px-3 text-sm font-semibold text-white hover:border-cyan/50"
            title="Speak latest response"
          >
            <Volume2 className="h-4 w-4" />
            {isSpeaking ? "Speaking" : "Speak"}
          </button>
        </div>
      </div>

      <div className="mt-4 border border-mint/25 bg-[linear-gradient(135deg,rgba(124,240,166,0.12),rgba(46,233,211,0.06),rgba(2,6,23,0.42))] p-4">
        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-mint">
              <Crown className="h-4 w-4" />
              <span>EXECUTIVE VOICE DEMO</span>
              <span className="border border-mint/30 px-2 py-1 text-[10px]">{ceoDemoRunning ? "analyzing" : "ready"}</span>
            </div>
            <h3 className="mt-2 text-xl font-semibold text-white">Talk To The CEO</h3>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">
              One button asks <span className="text-white">{CEO_DEMO_COMMAND}</span>, then automatically updates heatmaps, forecasts, digital twins, AI Agent Council reasoning, and executive recovery recommendations while the response is spoken.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void runCeoDemo()}
            disabled={ceoDemoRunning}
            className="inline-flex min-h-12 items-center justify-center gap-2 border border-mint/50 bg-mint/15 px-5 text-sm font-semibold text-mint transition hover:bg-mint/20 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {ceoDemoRunning ? <Radio className="h-4 w-4 animate-pulse" /> : <PlayCircle className="h-4 w-4" />}
            {ceoDemoRunning ? "AI Talking Back" : "Talk To The CEO"}
          </button>
        </div>
        <div className="mt-4 grid gap-2 md:grid-cols-5">
          {CEO_DEMO_STEPS.map((step, index) => {
            const active = index <= ceoDemoStep;
            return (
              <div key={step} className={`min-h-20 border p-3 ${active ? "border-mint/35 bg-mint/10 text-white" : "border-line bg-black/20 text-slate-500"}`}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[10px] uppercase">Step {index + 1}</span>
                  {active ? <CheckCircle2 className="h-4 w-4 text-mint" /> : <span className="h-2 w-2 rounded-full bg-slate-700" />}
                </div>
                <p className="mt-2 text-xs leading-5">{step}</p>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-4">
          <div className="flex gap-2">
            <input
              value={command}
              onChange={(event) => setCommand(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void executeCommand();
              }}
              className="min-h-11 flex-1 border border-line bg-black/25 px-3 text-sm text-white outline-none focus:border-cyan"
              placeholder="Ask: Which department needs attention?"
            />
            <button
              type="button"
              onClick={() => void executeCommand()}
              className="inline-flex h-11 items-center gap-2 border border-cyan/40 bg-cyan/10 px-4 text-sm font-semibold text-cyan"
              title="Send command"
            >
              <Send className="h-4 w-4" />
              Run
            </button>
          </div>

          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
            {EXECUTIVE_COMMANDS.map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => void executeCommand(item)}
                className="min-h-10 border border-line bg-white/[0.03] px-3 py-2 text-left text-xs text-slate-300 hover:border-cyan/40 hover:text-white"
              >
                {item}
              </button>
            ))}
          </div>

          <div className="border border-line bg-black/20 p-4">
            <div className="flex items-center justify-between gap-3 text-xs uppercase text-slate-500">
              <span>Live Transcript</span>
              <span>{current?.recognizedIntent.replaceAll("_", " ") ?? "awaiting command"}</span>
            </div>
            <p className="mt-2 min-h-12 text-sm leading-6 text-white">{liveTranscript || "Microphone or typed command transcript appears here."}</p>
          </div>

          {current ? (
            <div className="border border-cyan/20 bg-cyan/5 p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
                <Brain className="h-4 w-4" />
                <span>{current.targetDashboard}</span>
                <span>{Math.round(current.confidence * 100)}% confidence</span>
                <span>{current.latencyMs} ms</span>
              </div>
              <p className="mt-3 text-base leading-7 text-white">{current.answer}</p>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={controlDashboard}
                  className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-xs font-semibold text-cyan"
                >
                  <Zap className="h-4 w-4" />
                  {current.dashboardControl.targetLabel}
                </button>
                {current.actions.slice(0, 3).map((action) => (
                  <span key={`${action.target}-${action.label}`} className="inline-flex items-center gap-2 border border-line bg-black/20 px-3 py-2 text-xs text-slate-300">
                    <Workflow className="h-4 w-4 text-cyan" />
                    {action.label}
                  </span>
                ))}
              </div>
            </div>
          ) : null}

          {isJudgeDemoResult ? (
            <div className="border border-mint/25 bg-black/25 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="text-xs uppercase text-mint">Live Enterprise Impact</div>
                  <h3 className="mt-1 text-lg font-semibold text-white">AI Talks Back Executive Sequence</h3>
                </div>
                <span className="border border-mint/30 bg-mint/10 px-2 py-1 text-[10px] uppercase text-mint">automatic</span>
              </div>
              <div className="mt-4 grid gap-2 md:grid-cols-2">
                {JUDGE_IMPACT_STAGES.map(([label, detail], index) => (
                  <div key={label} className="border border-mint/20 bg-mint/[0.06] p-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-white">{label}</span>
                      <span className="h-2 w-2 animate-pulse rounded-full bg-mint" />
                    </div>
                    <p className="mt-2 min-h-10 text-xs leading-5 text-slate-300">{detail}</p>
                    <div className="mt-3 h-1.5 bg-white/10">
                      <div
                        className="h-1.5 bg-mint transition-all duration-700"
                        style={{ width: `${Math.min(100, 42 + index * 9 + Math.round(current.riskScore / 12))}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                {["Current Company", "Future Company", "Predicted Outcome"].map((label, index) => {
                  const value = Math.max(8, Math.round(100 - current.riskScore * (0.16 + index * 0.18)));
                  return (
                    <div key={label} className="border border-line bg-white/[0.03] p-3">
                      <div className="text-[10px] uppercase text-slate-500">{label}</div>
                      <div className="mt-2 text-2xl font-semibold text-white">{value}%</div>
                      <div className="mt-2 h-1.5 bg-white/10">
                        <div className="h-1.5 bg-cyan transition-all duration-700" style={{ width: `${value}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}

          {error ? <div className="border border-red-400/30 bg-red-500/10 p-3 text-sm text-red-100">{error}</div> : null}
        </div>

        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-4">
            <Metric label="Risk" value={current ? `${Math.round(current.riskScore)}%` : "--"} icon={Shield} />
            <Metric label="Memory" value={current ? `${current.conversationMemory.length}` : "0"} icon={History} />
            <Metric label="Sources" value={current ? `${current.sourceSystems.length}` : "0"} icon={Radio} />
            <Metric label="Readiness" value={current ? `${Math.round(current.productionReadinessScore)}` : "--"} icon={Zap} />
          </div>

          {current?.visualResponse ? (
            <div className="border border-cyan/20 bg-cyan/5 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-white">Visual Executive Response</h3>
                <span className="border border-cyan/30 bg-cyan/10 px-2 py-1 text-[10px] uppercase text-cyan">
                  {current.finalVerdict}
                </span>
              </div>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                {current.visualResponse.kpis.map((kpi) => (
                  <div key={kpi.label} className="border border-line bg-black/20 p-3">
                    <div className="text-[10px] uppercase text-slate-500">{kpi.label}</div>
                    <div className="mt-1 text-xl font-semibold text-white">{kpi.value}</div>
                    <div className="mt-1 text-[11px] text-cyan">{kpi.trend}</div>
                  </div>
                ))}
              </div>
              <div className="mt-3 space-y-3">
                {current.visualResponse.charts.map((chart) => (
                  <div key={chart.title} className="border border-line bg-black/20 p-3">
                    <div className="text-xs font-semibold uppercase text-slate-400">{chart.title}</div>
                    <div className="mt-3 space-y-2">
                      {chart.data.map((point) => {
                        const label = String(point.label ?? "Metric");
                        const value = Number(point.value ?? 0);
                        return (
                          <div key={`${chart.title}-${label}`} className="grid grid-cols-[110px_1fr_44px] items-center gap-2 text-xs">
                            <span className="truncate text-slate-400">{label}</span>
                            <span className="h-2 bg-white/10">
                              <span className="block h-2 bg-cyan" style={{ width: `${Math.max(4, Math.min(100, value))}%` }} />
                            </span>
                            <span className="text-right text-white">{Math.round(value)}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {current?.aiCouncil?.length ? (
            <div className="border border-line bg-black/20 p-4">
              <h3 className="text-sm font-semibold text-white">Executive AI Council</h3>
              <div className="mt-3 space-y-2">
                {current.aiCouncil.map((turn) => (
                  <div key={`${turn.agent}-${turn.role}`} className="border border-line bg-white/[0.03] p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-sm font-semibold text-white">{turn.agent}</span>
                      <span className="text-xs text-cyan">{Math.round(turn.confidence * 100)}%</span>
                    </div>
                    <div className="mt-1 text-[11px] uppercase text-slate-500">{turn.role}</div>
                    <p className="mt-2 text-xs leading-5 text-slate-300">{turn.finding}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="border border-line bg-black/20 p-4">
            <h3 className="text-sm font-semibold text-white">AI Recommendations</h3>
            <div className="mt-3 space-y-2">
              {(current?.recommendations ?? ["Run a command to generate grounded executive actions."]).slice(0, 5).map((item) => (
                <div key={item} className="border border-line bg-white/[0.03] p-3 text-sm leading-5 text-slate-300">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="border border-line bg-black/20 p-4">
            <h3 className="text-sm font-semibold text-white">Grounded Systems</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {sourceSystems.map((item) => (
                <span key={item} className="border border-cyan/20 bg-cyan/5 px-2 py-1 text-[11px] text-cyan">
                  {item.replaceAll("_", " ")}
                </span>
              ))}
            </div>
            {current?.analyticsCoverage?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {current.analyticsCoverage.map((item) => (
                  <span key={item} className="border border-mint/20 bg-mint/5 px-2 py-1 text-[11px] text-mint">
                    {item.replaceAll("_", " ")}
                  </span>
                ))}
              </div>
            ) : null}
          </div>

          {current?.voiceCapabilities?.length ? (
            <div className="border border-line bg-black/20 p-4">
              <h3 className="text-sm font-semibold text-white">Voice Readiness</h3>
              <div className="mt-3 grid gap-2">
                {current.voiceCapabilities.map((capability) => (
                  <div key={capability.capability} className="flex items-center justify-between gap-3 border border-line bg-white/[0.03] px-3 py-2">
                    <span className="text-xs text-slate-300">{capability.capability}</span>
                    <span className={`border px-2 py-1 text-[10px] uppercase ${
                      capability.status === "ready" ? "border-mint/30 text-mint" : capability.status === "degraded" ? "border-amber/30 text-amber" : "border-red-400/30 text-red-100"
                    }`}>
                      {capability.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {current?.executiveReadiness ? (
            <div className="border border-line bg-black/20 p-4">
              <h3 className="text-sm font-semibold text-white">CEO Assistant Readiness</h3>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {Object.entries(current.executiveReadiness).map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between gap-3 border border-line bg-white/[0.03] px-3 py-2">
                    <span className="text-[11px] uppercase text-slate-500">{key.replace(/([A-Z])/g, " $1")}</span>
                    <span className={`text-[10px] uppercase ${value === "ready" ? "text-mint" : value === "degraded" ? "text-amber" : "text-red-100"}`}>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          <div className="border border-line bg-black/20 p-4">
            <h3 className="text-sm font-semibold text-white">Command Trace</h3>
            <div className="mt-3 space-y-2">
              {(current?.commandTrace ?? ["Awaiting command trace."]).map((item) => (
                <div key={item} className="border-l border-cyan/30 pl-3 text-xs leading-5 text-slate-400">
                  {item}
                </div>
              ))}
            </div>
          </div>

          <div className="border border-line bg-black/20 p-4">
            <h3 className="text-sm font-semibold text-white">Conversation Memory</h3>
            <div className="mt-3 space-y-3">
              {history.length ? (
                history.map((item) => (
                  <div key={`${item.generatedAt}-${item.transcript}`} className="border-l border-cyan/30 pl-3">
                    <div className="text-xs uppercase text-slate-500">{item.recognizedIntent.replaceAll("_", " ")}</div>
                    <div className="mt-1 text-sm text-white">{item.transcript}</div>
                    <div className="mt-1 line-clamp-2 text-xs leading-5 text-slate-400">{item.answer}</div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-400">Multi-turn context appears after the first command.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value, icon: Icon }: { label: string; value: string; icon: LucideIcon }) {
  return (
    <div className="border border-line bg-white/[0.03] p-3">
      <div className="flex items-center gap-2 text-xs uppercase text-slate-500">
        <Icon className="h-4 w-4 text-cyan" />
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}
