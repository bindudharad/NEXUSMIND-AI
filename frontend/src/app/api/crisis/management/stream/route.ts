const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";

async function token() {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Crisis command stream authentication failed");
  return ((await response.json()) as { access_token: string }).access_token;
}

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

function toCamelEvent(event: string): string {
  return event
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

export async function GET() {
  try {
    const accessToken = await token();
    const response = await fetch(`${API_BASE_URL}/crisis/management/stream`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.body) throw new Error("Missing crisis command stream");
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
            controller.enqueue(encoder.encode(`${toCamelEvent(event)}\n\n`));
          }
        },
        flush(controller) {
          buffer += decoder.decode();
          if (buffer.trim()) controller.enqueue(encoder.encode(toCamelEvent(buffer)));
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
    return new Response("event: error\ndata: {\"detail\":\"Crisis command stream failed\"}\n\n", {
      status: 500,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
