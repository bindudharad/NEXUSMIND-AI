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
  if (!response.ok) throw new Error("Recruiter impression stream authentication failed");
  return ((await response.json()) as { access_token: string }).access_token;
}

export async function GET() {
  try {
    const accessToken = await token();
    const response = await fetch(`${API_BASE_URL}/recruiter-impression/stream`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    if (!response.body) throw new Error("Missing recruiter impression stream");
    return new Response(response.body, {
      status: response.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  } catch {
    return new Response("event: error\ndata: {\"detail\":\"Recruiter impression stream failed\"}\n\n", {
      status: 500,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
