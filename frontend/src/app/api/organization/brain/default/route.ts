import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/organization/brain/default");
  } catch {
    return NextResponse.json({ detail: "Organizational Brain default graph failed" }, { status: 500 });
  }
}
