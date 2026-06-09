import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/knowledge/brain/default");
  } catch {
    return NextResponse.json({ detail: "Company Brain default load failed" }, { status: 500 });
  }
}
