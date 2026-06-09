import { NextResponse } from "next/server";

import { proxyJson } from "../../_proxy";

export async function GET(request: Request) {
  try {
    const url = new URL(request.url);
    const params = new URLSearchParams();
    const q = url.searchParams.get("q");
    const nodeType = url.searchParams.get("nodeType");
    if (q) params.set("q", q);
    if (nodeType) params.set("node_type", nodeType);
    const suffix = params.toString() ? `?${params.toString()}` : "";
    return await proxyJson(`/knowledge/brain/graph/query${suffix}`);
  } catch {
    return NextResponse.json({ detail: "Company Brain graph query failed" }, { status: 500 });
  }
}
