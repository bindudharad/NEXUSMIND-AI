import { NextResponse } from "next/server";

import { buildResilientVoiceStressResponse } from "@/app/api/voice/_resilient";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";
const VOICE_BACKEND_BUDGET_MS = Math.min(Number(process.env.API_TIMEOUT_MS ?? 4500), 4500);
const USE_LIVE_VOICE_BACKEND = process.env.VOICE_BACKEND_MODE === "live";

type SnakeRecord = Record<string, unknown>;

function toCamel(value: unknown): unknown {
  if (Array.isArray(value)) return value.map((item) => toCamel(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value as SnakeRecord).map(([key, nested]) => [
        key.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase()),
        toCamel(nested),
      ]),
    );
  }
  return value;
}

async function token() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Voice stress authentication failed");
  return ((await response.json()) as { access_token: string }).access_token;
}

async function fetchWithTimeout(input: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), VOICE_BACKEND_BUDGET_MS);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

export async function GET() {
  if (!USE_LIVE_VOICE_BACKEND) return NextResponse.json(buildResilientVoiceStressResponse());
  try {
    const accessToken = await token();
    const response = await fetchWithTimeout(`${API_BASE_URL}/voice/default`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Voice stress analysis failed");
    return NextResponse.json(toCamel(await response.json()), { status: response.status });
  } catch {
    return NextResponse.json(buildResilientVoiceStressResponse());
  }
}

export async function POST(request: Request) {
  const payload = await request.json().catch(() => ({}));
  if (!USE_LIVE_VOICE_BACKEND) return NextResponse.json(buildResilientVoiceStressResponse(payload));
  try {
    const accessToken = await token();
    const response = await fetchWithTimeout(`${API_BASE_URL}/voice/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Voice stress analysis failed");
    return NextResponse.json(toCamel(await response.json()), { status: response.status });
  } catch {
    return NextResponse.json(buildResilientVoiceStressResponse(payload));
  }
}
