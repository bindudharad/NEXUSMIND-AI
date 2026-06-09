import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    return await proxyJson("/knowledge/brain/ask", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch {
    return NextResponse.json({ detail: "Company Brain question failed" }, { status: 500 });
  }
}
