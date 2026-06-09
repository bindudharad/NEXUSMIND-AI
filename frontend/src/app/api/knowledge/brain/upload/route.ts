import { NextResponse } from "next/server";

import { API_BASE_URL, backendFetch, toCamel, token } from "../_proxy";

export async function POST(request: Request) {
  try {
    const accessToken = await token();
    const formData = await request.formData();
    const response = await backendFetch(`${API_BASE_URL}/knowledge/brain/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body: formData,
      cache: "no-store",
    });
    const payload = await response.json();
    return NextResponse.json(toCamel(payload), { status: response.status });
  } catch {
    return NextResponse.json({ detail: "Company Brain file upload failed" }, { status: 500 });
  }
}
