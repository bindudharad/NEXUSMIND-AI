import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    return await proxyJson("/organization/brain/assistant", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch {
    return NextResponse.json({ detail: "Organizational Brain assistant failed" }, { status: 500 });
  }
}
