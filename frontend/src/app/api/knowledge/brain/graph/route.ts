import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/knowledge/brain/graph");
  } catch {
    return NextResponse.json({ detail: "Company Brain graph failed" }, { status: 500 });
  }
}
