"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Activity, AudioLines, Loader2, Mic, Radio, RefreshCw, Send, ShieldAlert, Waves } from "lucide-react";

import type { VoiceAlert, VoiceCommandResponse, VoiceStressResponse } from "@/types/voice";

type SnakeRecord = Record<string, unknown>;
type AudioContextConstructor = typeof AudioContext;

const sampleTranscript =
  "I am exhausted and anxious because this project escalation keeps getting worse and the team is arguing.";
const sampleCommand = "Show highest-risk department.";

const severityColor: Record<VoiceAlert["severity"], string> = {
  low: "#7CF0A6",
  medium: "#F6B44B",
  high: "#F05D5E",
  critical: "#FF3B6B",
};

export function VoiceStressPanel() {
  const [analysis, setAnalysis] = useState<VoiceStressResponse | null>(null);
  const [transcript, setTranscript] = useState(sampleTranscript);
  const [loading, setLoading] = useState(true);
  const [recording, setRecording] = useState(false);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [commandText, setCommandText] = useState(sampleCommand);
  const [commandResult, setCommandResult] = useState<VoiceCommandResponse | null>(null);
  const [commandLoading, setCommandLoading] = useState(false);
  const cancelRecordingRef = useRef(false);

  const submitAnalysis = useCallback(async (audioSamples?: number[], mode: "calm" | "stressed" | "microphone" = "stressed", sampleRate = 16000) => {
    setLoading(true);
    setError("");
    try {
      const samples = audioSamples ?? buildAudioSample(mode === "calm" ? "calm" : "stressed", sampleRate);
      const response = await fetch("/api/voice/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employee_id: mode === "calm" ? "voice-calm" : "voice-live",
          speaker: mode === "calm" ? "Calm Employee" : "Live Speaker",
          department: "Engineering",
          transcript,
          source_format: "browser_pcm",
          sample_rate: sampleRate,
          duration_seconds: samples.length / sampleRate,
          audio_samples: samples,
        }),
        cache: "no-store",
      });
      if (!response.ok) throw new Error("Voice stress analysis failed");
      setAnalysis((await response.json()) as VoiceStressResponse);
    } catch {
      setError("Voice Stress Detection AI could not process the audio stream.");
    } finally {
      setLoading(false);
    }
  }, [transcript]);

  const loadSample = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/voice/analyze", { cache: "no-store" });
      if (!response.ok) throw new Error("Voice stress analysis failed");
      setAnalysis((await response.json()) as VoiceStressResponse);
    } catch {
      setError("Voice Stress Detection AI could not load the baseline signal.");
    } finally {
      setLoading(false);
    }
  }, []);

  const captureMicrophone = useCallback(async () => {
    const audioWindow = window as Window & { webkitAudioContext?: AudioContextConstructor };
    const AudioContextCtor = window.AudioContext ?? audioWindow.webkitAudioContext;
    if (!navigator.mediaDevices?.getUserMedia || !AudioContextCtor) {
      setError("Live microphone capture is unavailable in this browser.");
      return;
    }

    setRecording(true);
    setError("");
    cancelRecordingRef.current = false;
    let stream: MediaStream | null = null;
    let context: AudioContext | null = null;
    let source: MediaStreamAudioSourceNode | null = null;
    let processor: ScriptProcessorNode | null = null;
    const samples: number[] = [];

    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      context = new AudioContextCtor();
      source = context.createMediaStreamSource(stream);
      processor = context.createScriptProcessor(2048, 1, 1);
      processor.onaudioprocess = (event) => {
        if (cancelRecordingRef.current) return;
        const input = event.inputBuffer.getChannelData(0);
        for (let index = 0; index < input.length && samples.length < 190000; index += 1) {
          samples.push(Number(input[index].toFixed(5)));
        }
      };
      source.connect(processor);
      processor.connect(context.destination);
      await new Promise((resolve) => window.setTimeout(resolve, 3800));
      cancelRecordingRef.current = true;
      const sampleRate = context.sampleRate || 48000;
      await submitAnalysis(samples, "microphone", sampleRate);
    } catch {
      setError("Microphone capture failed. Synthetic acoustic analysis remains available.");
    } finally {
      cancelRecordingRef.current = true;
      processor?.disconnect();
      source?.disconnect();
      stream?.getTracks().forEach((track) => track.stop());
      if (context && context.state !== "closed") await context.close();
      setRecording(false);
    }
  }, [submitAnalysis]);

  const executeCommand = useCallback(async () => {
    setCommandLoading(true);
    setError("");
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch("/api/voice/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript: commandText,
          speaker: "Executive Operator",
          department: "Executive",
          include_spoken_response: true,
        }),
        cache: "no-store",
        signal: controller.signal,
      });
      if (!response.ok) throw new Error("Voice command execution failed");
      setCommandResult((await response.json()) as VoiceCommandResponse);
    } catch {
      setError("Voice Command AI could not execute the enterprise command.");
    } finally {
      window.clearTimeout(timeout);
      setCommandLoading(false);
    }
  }, [commandText]);

  useEffect(() => {
    const controller = new AbortController();

    async function connectStream() {
      try {
        const response = await fetch("/api/voice/stream", { cache: "no-store", signal: controller.signal });
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Missing voice stream");
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
              setAnalysis(toCamel<VoiceStressResponse>(JSON.parse(dataLine.slice(6))));
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
      void loadSample();
    }, 9800);
    const streamRefresh = window.setTimeout(() => {
      void connectStream();
    }, 17000);
    return () => {
      controller.abort();
      window.clearTimeout(firstRefresh);
      window.clearTimeout(streamRefresh);
      cancelRecordingRef.current = true;
    };
  }, [loadSample]);

  const timeline = useMemo(
    () =>
      analysis?.timeline.map((point) => ({
        second: point.second,
        stress: Math.round(point.stress),
        pitch: Math.round(point.pitchHz),
      })) ?? [],
    [analysis],
  );

  const emotionEntries = useMemo(() => Object.entries(analysis?.emotionScores ?? {}), [analysis]);
  const waveformPoints = useMemo(() => {
    if (!analysis?.timeline.length) return "";
    return analysis.timeline
      .map((point, index) => {
        const x = (index / Math.max(analysis.timeline.length - 1, 1)) * 600;
        const y = 118 - Math.min(110, point.intensity * 620 + point.stress * 0.55);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");
  }, [analysis]);

  return (
    <section className="border border-line/80 bg-panel/85 p-5 shadow-control backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <AudioLines className="size-5 text-cyan" />
          <div>
            <p className="text-xs uppercase text-cyan">Voice Stress Detection AI</p>
            <h2 className="text-xl font-semibold text-white">Acoustic stress, transcript sentiment, live alerts, and emotional trend fusion</h2>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => void loadSample()} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-slate-300">
            <RefreshCw className="size-4" />
            Load sample
          </button>
          <button onClick={() => void submitAnalysis(undefined, "calm")} className="inline-flex items-center gap-2 border border-line bg-panel2 px-3 py-2 text-sm text-mint">
            <Waves className="size-4" />
            Calm signal
          </button>
          <button onClick={() => void submitAnalysis()} className="inline-flex items-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-sm text-cyan">
            {loading ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Analyze voice
          </button>
          <button
            onClick={() => void captureMicrophone()}
            disabled={recording}
            className="inline-flex items-center gap-2 border border-signal/40 bg-signal/10 px-3 py-2 text-sm text-signal disabled:cursor-not-allowed disabled:opacity-60"
          >
            {recording ? <Loader2 className="size-4 animate-spin" /> : <Mic className="size-4" />}
            {recording ? "Listening" : "Mic capture"}
          </button>
        </div>
      </div>

      <textarea
        value={transcript}
        onChange={(event) => setTranscript(event.target.value)}
        className="mt-5 min-h-24 w-full resize-none border border-line bg-void/70 p-4 text-sm leading-6 text-slate-100 outline-none transition focus:border-cyan/50"
      />

      <div className="mt-4 grid gap-3 border border-line/70 bg-panel2/65 p-4 xl:grid-cols-[1fr_auto]">
        <input
          value={commandText}
          onChange={(event) => setCommandText(event.target.value)}
          className="min-h-11 border border-line bg-void/70 px-3 text-sm text-slate-100 outline-none transition focus:border-mint/50"
          aria-label="Enterprise voice command"
        />
        <button
          onClick={() => void executeCommand()}
          disabled={commandLoading}
          className="inline-flex items-center justify-center gap-2 border border-mint/40 bg-mint/10 px-3 py-2 text-sm text-mint disabled:cursor-not-allowed disabled:opacity-60"
        >
          {commandLoading ? <Loader2 className="size-4 animate-spin" /> : <Radio className="size-4" />}
          Run command
        </button>
      </div>

      {commandResult ? (
        <article className="mt-4 border border-mint/30 bg-mint/10 p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase text-mint">{commandResult.recognizedIntent.replace(/_/g, " ")}</p>
              <h3 className="text-base font-semibold text-white">{commandResult.targetDashboard}</h3>
            </div>
            <span className="text-xs uppercase text-mint">
              {Math.round(commandResult.confidence * 100)}% / risk {Math.round(commandResult.riskScore)}
            </span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-200">{commandResult.spokenResponse}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {commandResult.actions.map((action) => (
              <span key={`${action.actionType}-${action.target}`} className="border border-line/70 bg-void/60 px-3 py-1 text-xs text-slate-400">
                {action.label}
              </span>
            ))}
          </div>
        </article>
      ) : null}

      {error ? <p className="mt-4 text-sm text-signal">{error}</p> : null}
      {loading ? <p className="mt-5 text-sm text-slate-400">Analyzing pitch variance, vocal tension, transcript pressure, and burnout markers...</p> : null}

      {analysis ? (
        <>
          <div className="mt-5 grid gap-3 md:grid-cols-6">
            <Stat label="Stress" value={`${Math.round(analysis.stressScore)}%`} />
            <Stat label="Burnout" value={`${Math.round(analysis.burnoutRisk)}%`} />
            <Stat label="Conflict" value={`${Math.round(analysis.conflictIntensity)}%`} />
            <Stat label="Pressure" value={`${Math.round(analysis.communicationPressure)}%`} />
            <Stat label="Emotion" value={analysis.primaryEmotion} />
            <Stat label="Stream" value={streamStatus} />
          </div>

          <div className="mt-5 grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
                <Activity className="size-4" />
                Voice timeline
              </div>
              <div className="mb-4 border border-line/60 bg-void/60 p-3">
                <svg viewBox="0 0 600 130" role="img" aria-label="Voice stress waveform" className="h-28 w-full">
                  <defs>
                    <linearGradient id="voiceWave" x1="0" x2="1" y1="0" y2="0">
                      <stop offset="0%" stopColor="#2EE9D3" />
                      <stop offset="55%" stopColor="#F6B44B" />
                      <stop offset="100%" stopColor="#FF3B6B" />
                    </linearGradient>
                  </defs>
                  <line x1="0" x2="600" y1="112" y2="112" stroke="#263241" strokeDasharray="4 6" />
                  <polyline points={waveformPoints} fill="none" stroke="url(#voiceWave)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={timeline} margin={{ left: -22, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid stroke="#263241" strokeDasharray="3 3" />
                    <XAxis dataKey="second" stroke="#64748b" tickLine={false} axisLine={false} tick={{ fontSize: 11 }} />
                    <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                    <Tooltip contentStyle={{ background: "#0B1017", border: "1px solid #263241", color: "#eef7fb" }} />
                    <Area type="monotone" dataKey="stress" stroke="#FF3B6B" fill="#FF3B6B" fillOpacity={0.18} />
                    <Area type="monotone" dataKey="pitch" stroke="#2EE9D3" fill="#2EE9D3" fillOpacity={0.08} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-mint">
                <Radio className="size-4" />
                Audio + NLP fusion
              </div>
              <div className="grid gap-3">
                {emotionEntries.map(([emotion, score]) => (
                  <div key={emotion}>
                    <div className="mb-1 flex justify-between text-xs uppercase text-slate-500">
                      <span>{emotion}</span>
                      <span>{Math.round(Number(score) * 100)}%</span>
                    </div>
                    <div className="h-2 bg-void">
                      <div className="h-2 bg-cyan" style={{ width: `${Math.round(Number(score) * 100)}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid gap-2 text-xs leading-5 text-slate-400">
                {analysis.fusionEvidence.map((item) => (
                  <span key={item} className="border border-line/50 bg-panel/55 px-3 py-2">
                    {item}
                  </span>
                ))}
              </div>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-signal">
                <ShieldAlert className="size-4" />
                Voice alerts
              </div>
              <div className="grid gap-3">
                {(analysis.alerts.length ? analysis.alerts : emptyAlerts()).map((alert) => (
                  <div key={`${alert.category}-${alert.message}`} className="border border-line/60 bg-panel/60 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h3 className="text-sm font-medium capitalize text-white">{alert.category.replace(/_/g, " ")}</h3>
                      <span style={{ color: severityColor[alert.severity] }} className="text-xs uppercase">
                        {alert.severity} / {Math.round(alert.score)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-5 text-slate-300">{alert.message}</p>
                    <p className="mt-2 text-xs leading-5 text-slate-500">{alert.recommendation}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="border border-line/70 bg-panel2/65 p-4">
              <div className="mb-3 flex items-center gap-2 text-xs uppercase text-amber">
                <Waves className="size-4" />
                Acoustic fingerprint
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <Feature label="Pitch mean" value={`${Math.round(analysis.acousticFeatures.pitchMeanHz)} Hz`} />
                <Feature label="Pitch variation" value={`${Math.round(analysis.acousticFeatures.pitchVariation)} Hz`} />
                <Feature label="Vocal tension" value={`${Math.round(analysis.acousticFeatures.vocalTension)}/100`} />
                <Feature label="Speech rate" value={`${Math.round(analysis.acousticFeatures.speechRateWpm)} wpm`} />
                <Feature label="Pause ratio" value={`${Math.round(analysis.acousticFeatures.pauseRatio * 100)}%`} />
                <Feature label="Tremor proxy" value={analysis.acousticFeatures.tremorProxy.toFixed(3)} />
              </div>
              <div className="mt-4 grid gap-2 text-sm leading-6 text-slate-300">
                {analysis.recommendations.map((item) => (
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

function buildAudioSample(mode: "calm" | "stressed", sampleRate = 16000, seconds = 3.2) {
  const length = Math.round(sampleRate * seconds);
  const samples: number[] = [];
  for (let index = 0; index < length; index += 1) {
    const time = index / sampleRate;
    if (mode === "calm") {
      samples.push(Number((0.15 * Math.sin(2 * Math.PI * 178 * time) + 0.015 * Math.sin(2 * Math.PI * 3.2 * time)).toFixed(5)));
    } else {
      const modulation = 1 + 0.28 * Math.sin(2 * Math.PI * 7.2 * time);
      const variablePitch = 255 + 42 * Math.sin(2 * Math.PI * 4.8 * time);
      const voice = 0.28 * modulation * Math.sin(2 * Math.PI * variablePitch * time);
      const tension = 0.05 * Math.sin(2 * Math.PI * 1160 * time) + 0.035 * Math.sin(2 * Math.PI * 1450 * time);
      const tremor = 0.025 * Math.sin(2 * Math.PI * 11 * time);
      samples.push(Number(Math.max(-1, Math.min(1, voice + tension + tremor)).toFixed(5)));
    }
  }
  return samples;
}

function emptyAlerts(): VoiceAlert[] {
  return [
    {
      category: "stable_voice_signal",
      severity: "low",
      score: 18,
      message: "Voice signal is currently stable.",
      evidence: [],
      recommendation: "Maintain the current meeting cadence.",
    },
  ];
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/70 bg-panel2/65 p-3">
      <span className="block text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block break-words text-base text-white">{value}</strong>
    </div>
  );
}

function Feature({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-line/60 bg-panel/60 p-3">
      <span className="text-xs uppercase text-slate-500">{label}</span>
      <strong className="mt-1 block text-sm text-white">{value}</strong>
    </div>
  );
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
