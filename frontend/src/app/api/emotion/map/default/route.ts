import { NextResponse } from "next/server";

import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/emotion/map/default");
  } catch {
    return NextResponse.json({ detail: "Company emotion map default analysis failed" }, { status: 500 });
  }
}
