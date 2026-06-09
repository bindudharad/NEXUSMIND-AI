import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";
const BACKEND_TIMEOUT_MS = Number(process.env.API_TIMEOUT_MS ?? 45000);
const BACKEND_ATTEMPTS = 3;

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

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithTimeout(input: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function backendFetch(input: string, init: RequestInit = {}) {
  let lastError: unknown;
  for (let attempt = 1; attempt <= BACKEND_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetchWithTimeout(input, init);
      if (response.ok || response.status < 500 || attempt === BACKEND_ATTEMPTS) return response;
      lastError = new Error(`Backend returned ${response.status}`);
    } catch (error) {
      lastError = error;
      if (attempt === BACKEND_ATTEMPTS) throw error;
    }
    await wait(250 * attempt);
  }
  throw lastError instanceof Error ? lastError : new Error("Knowledge loss backend request failed");
}

async function readJson(response: Response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return { detail: text.slice(0, 500) };
  }
}

async function token() {
  const response = await backendFetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Knowledge loss authentication failed");
  return ((await readJson(response)) as { access_token: string }).access_token;
}

export async function GET() {
  try {
    const accessToken = await token();
    const response = await backendFetch(`${API_BASE_URL}/knowledge/loss/default`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    return NextResponse.json(toCamel(await readJson(response)), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "Knowledge loss analysis failed" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const accessToken = await token();
    const payload = await request.json();
    const response = await backendFetch(`${API_BASE_URL}/knowledge/loss/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    return NextResponse.json(toCamel(await readJson(response)), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "Knowledge loss analysis failed" }, { status: 500 });
  }
}
