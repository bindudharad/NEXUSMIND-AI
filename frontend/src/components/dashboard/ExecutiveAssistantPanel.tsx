"use client";

import gsap from "gsap";
import { AudioLines, Mic, Play, Sparkles, Volume2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { ExecutiveDirective } from "@/types/intelligence";

type SpeechRecognitionResultLike = {
  0: {
    transcript: string;
  };
};

type SpeechRecognitionEventLike = {
  results: {
    length: number;
    [index: number]: SpeechRecognitionResultLike;
  };
};

type BrowserSpeechRecognition = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onend: (() => void) | null;
  onerror: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

export function ExecutiveAssistantPanel({ directives }: { directives: ExecutiveDirective[] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [voiceStatus, setVoiceStatus] = useState("Voice engine standing by");
  const pulseRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);
  const active = directives[activeIndex];

  useEffect(() => {
    if (!pulseRef.current) return;
    const animation = gsap.to(pulseRef.current, {
      scale: 1.12,
      opacity: 0.35,
      duration: 1.2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });
    return () => {
      animation.kill();
    };
  }, []);

  function selectDirective(commandText: string) {
    const normalized = commandText.toLowerCase();
    const scored = directives.map((directive, index) => {
      const words = directive.command.toLowerCase().split(/\W+/).filter(Boolean);
      const score = words.reduce((total, word) => total + (normalized.includes(word) ? 1 : 0), 0);
      return { index, score };
    });
    const winner = scored.sort((a, b) => b.score - a.score)[0];
    const nextIndex = winner?.score ? winner.index : activeIndex;
    setActiveIndex(nextIndex);
    return directives[nextIndex];
  }

  function speakDirective(directive = active) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      setVoiceStatus("Speech output is unavailable in this browser");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(directive.answer);
    utterance.rate = 0.94;
    utterance.pitch = 0.82;
    utterance.volume = 0.92;
    window.speechSynthesis.speak(utterance);
    setVoiceStatus(`Speaking: ${directive.command}`);
  }

  function startVoiceCommand() {
    if (typeof window === "undefined") return;
    const voiceWindow = window as Window & {
      SpeechRecognition?: SpeechRecognitionConstructor;
      webkitSpeechRecognition?: SpeechRecognitionConstructor;
    };
    const Recognition = voiceWindow.SpeechRecognition ?? voiceWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setVoiceStatus("Speech recognition is unavailable; use command playback");
      return;
    }
    const recognition = new Recognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";
    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1]?.[0]?.transcript ?? "";
      setTranscript(result);
      const directive = selectDirective(result);
      speakDirective(directive);
    };
    recognition.onerror = () => {
      setListening(false);
      setVoiceStatus("Voice recognition could not complete this command");
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };
    recognitionRef.current = recognition;
    setListening(true);
    setVoiceStatus("Listening for executive command");
    recognition.start();
  }

  function stopVoiceCommand() {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setListening(false);
    setVoiceStatus("Voice command stopped");
  }

  return (
    <section className="relative overflow-hidden border border-cyan/25 bg-panel/90 p-5 shadow-control backdrop-blur">
      <div className="absolute right-5 top-5 grid size-16 place-items-center">
        <div ref={pulseRef} className="absolute size-16 rounded-full bg-cyan/25" />
        <div className="relative grid size-12 place-items-center rounded-full border border-cyan/50 bg-cyan/15">
          <AudioLines className="size-5 text-cyan" />
        </div>
      </div>

      <div className="pr-20">
        <p className="text-xs uppercase text-cyan">Live CEO Assistant</p>
        <h2 className="mt-2 text-2xl font-semibold text-white">Executive voice command layer</h2>
        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-400">{active.answer}</p>
      </div>

      <div className="mt-6 grid gap-3">
        {directives.map((directive, index) => (
          <button
            key={directive.command}
            onClick={() => setActiveIndex(index)}
            className={`flex items-center justify-between gap-4 border p-3 text-left transition ${
              index === activeIndex
                ? "border-cyan/50 bg-cyan/10"
                : "border-line/70 bg-panel2/60 hover:border-ion/50"
            }`}
          >
            <span>
              <span className="flex items-center gap-2 text-sm font-medium text-white">
                <Mic className="size-4 text-cyan" />
                {directive.command}
              </span>
              <span className="mt-1 block text-xs text-slate-500">{directive.action}</span>
            </span>
            <span className="flex items-center gap-2 text-sm text-mint">
              <Sparkles className="size-4" />
              {directive.confidence}%
            </span>
          </button>
        ))}
      </div>

      <div className="mt-5 grid gap-3 border border-line/70 bg-void/60 p-3 text-sm text-slate-300 sm:grid-cols-[1fr_auto_auto] sm:items-center">
        <div className="flex items-center gap-3">
          <Play className="size-4 text-cyan" />
          <span>
            {voiceStatus}
            {transcript ? <span className="block text-xs text-slate-500">Heard: {transcript}</span> : null}
          </span>
        </div>
        <button
          type="button"
          onClick={() => (listening ? stopVoiceCommand() : startVoiceCommand())}
          className="inline-flex items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-3 py-2 text-cyan"
        >
          <Mic className="size-4" />
          {listening ? "Stop" : "Listen"}
        </button>
        <button
          type="button"
          onClick={() => speakDirective()}
          className="inline-flex items-center justify-center gap-2 border border-line bg-panel2 px-3 py-2 text-slate-300"
        >
          <Volume2 className="size-4" />
          Speak
        </button>
      </div>
    </section>
  );
}
