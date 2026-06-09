import { NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

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

export async function GET() {
  try {
    const response = await fetch(`${API_BASE_URL}/system/technology-stack`, { cache: "no-store" });
    return NextResponse.json(toCamel(await response.json()), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "Technology stack verification failed" }, { status: 500 });
  }
}
