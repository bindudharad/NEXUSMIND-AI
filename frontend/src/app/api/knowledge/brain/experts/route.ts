import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const skill = url.searchParams.get("skill");
    const suffix = skill ? `?skill=${encodeURIComponent(skill)}` : "";
    return await proxyJson(`/knowledge/brain/experts${suffix}`);
  } catch {
    return NextResponse.json({ detail: "Company Brain experts failed" }, { status: 500 });
  }
}
