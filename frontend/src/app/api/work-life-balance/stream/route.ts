const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";
const BACKEND_TIMEOUT_MS = Number(process.env.API_TIMEOUT_MS ?? 45000);
const BACKEND_ATTEMPTS = 3;

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
  for (let attempt = 1; attempt <= BACKEND_ATTEMPTS; attempt += 1) {
    try {
      const response = await fetchWithTimeout(input, init);
      if (response.ok || response.status < 500 || attempt === BACKEND_ATTEMPTS) return response;
    } catch (error) {
      if (attempt === BACKEND_ATTEMPTS) throw error;
    }
    await wait(250 * attempt);
  }
  throw new Error("Work-life balance stream backend request failed");
}

async function token() {
  const response = await backendFetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Work-life balance stream authentication failed");
  return ((await response.json()) as { access_token: string }).access_token;
}

function toCamelJsonText(chunk: string): string {
  return chunk.replace(/_([a-z])/g, (_, letter: string) => letter.toUpperCase());
}

function transformSseEvent(eventBlock: string): string {
  return eventBlock
    .split("\n")
    .map((line) => {
      if (!line.startsWith("data: ")) return line;
      return `data: ${toCamelJsonText(line.slice(6))}`;
    })
    .join("\n");
}

export async function GET() {
  try {
    const accessToken = await token();
    const response = await backendFetch(`${API_BASE_URL}/work-life/balance/stream`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.ok || !response.body) throw new Error("Missing work-life balance stream");
    const decoder = new TextDecoder();
    const encoder = new TextEncoder();
    let buffer = "";
    const stream = response.body.pipeThrough(
      new TransformStream<Uint8Array, Uint8Array>({
        transform(chunk, controller) {
          buffer += decoder.decode(chunk, { stream: true });
          const events = buffer.split("\n\n");
          buffer = events.pop() ?? "";
          for (const event of events) {
            controller.enqueue(encoder.encode(`${transformSseEvent(event)}\n\n`));
          }
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
  } catch {
    return new Response("event: error\ndata: {\"detail\":\"Work-life balance stream failed\"}\n\n", {
      status: 500,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
