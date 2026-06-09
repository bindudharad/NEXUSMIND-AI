import { NextResponse } from "next/server";

export const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";
const BACKEND_TIMEOUT_MS = Number(process.env.API_TIMEOUT_MS ?? 45000);

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

async function backendFetch(input: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
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
  if (!response.ok) throw new Error("Talent marketplace authentication failed");
  return ((await readJson(response)) as { access_token: string }).access_token;
}

export async function proxyJson(path: string, init: RequestInit = {}) {
  const accessToken = await token();
  const response = await backendFetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(init.headers ?? {}),
      Authorization: `Bearer ${accessToken}`,
    },
    cache: "no-store",
  });
  return NextResponse.json(toCamel(await readJson(response)), { status: response.status });
}

function transformSseEvent(eventBlock: string): string {
  return eventBlock
    .split("\n")
    .map((line) => {
      if (!line.startsWith("data: ")) return line;
      try {
        return `data: ${JSON.stringify(toCamel(JSON.parse(line.slice(6))))}`;
      } catch {
        return line;
      }
    })
    .join("\n");
}

export async function proxyStream(path: string) {
  const accessToken = await token();
  const response = await backendFetch(`${API_BASE_URL}${path}`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok || !response.body) throw new Error("Missing talent marketplace stream");
  const decoder = new TextDecoder();
  const encoder = new TextEncoder();
  let buffer = "";
  const stream = response.body.pipeThrough(
    new TransformStream<Uint8Array, Uint8Array>({
      transform(chunk, controller) {
        buffer += decoder.decode(chunk, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";
        for (const event of events) controller.enqueue(encoder.encode(`${transformSseEvent(event)}\n\n`));
      },
      flush(controller) {
        const tail = decoder.decode();
        if (tail) buffer += tail;
        if (buffer) controller.enqueue(encoder.encode(transformSseEvent(buffer)));
      },
    }),
  );
  return new Response(stream, {
    status: response.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
