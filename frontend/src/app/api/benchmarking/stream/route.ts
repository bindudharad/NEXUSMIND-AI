const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
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

async function fetchWithTimeout(input: string, init: RequestInit = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}

async function token() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Benchmarking authentication failed");
  return ((await response.json()) as { access_token: string }).access_token;
}

function transformSseChunk(chunk: string) {
  return chunk
    .split("\n\n")
    .map((event) => {
      const lines = event.split("\n");
      return lines
        .map((line) => {
          if (!line.startsWith("data: ")) return line;
          try {
            return `data: ${JSON.stringify(toCamel(JSON.parse(line.slice(6))))}`;
          } catch {
            return line;
          }
        })
        .join("\n");
    })
    .join("\n\n");
}

export async function GET() {
  try {
    const accessToken = await token();
    const response = await fetch(`${API_BASE_URL}/benchmarks/companies/stream`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok || !response.body) {
      return new Response("event: error\ndata: {\"detail\":\"Benchmarking stream failed\"}\n\n", {
        status: 502,
        headers: { "Content-Type": "text/event-stream" },
      });
    }
    const decoder = new TextDecoder();
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body?.getReader();
        if (!reader) {
          controller.close();
          return;
        }
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(encoder.encode(transformSseChunk(decoder.decode(value, { stream: true }))));
        }
        controller.close();
      },
    });
    return new Response(stream, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return new Response("event: error\ndata: {\"detail\":\"Benchmarking stream failed\"}\n\n", {
      status: 500,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
