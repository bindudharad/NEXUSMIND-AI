import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
const DEMO_EMAIL = process.env.DEMO_EMAIL ?? "ceo@nexusmind.ai";
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? "nexusmind-demo";

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
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: DEMO_EMAIL, password: DEMO_PASSWORD }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("Crisis command center authentication failed");
  return ((await response.json()) as { access_token: string }).access_token;
}

export async function GET() {
  try {
    const accessToken = await token();
    const response = await fetch(`${API_BASE_URL}/crisis/management/default`, {
      headers: { Authorization: `Bearer ${accessToken}` },
      cache: "no-store",
    });
    return NextResponse.json(toCamel(await response.json()), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "Crisis command center failed" }, { status: 500 });
  }
}
