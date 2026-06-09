import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    const payload = await request.json();
    return await proxyJson("/competitive/intelligence/analyze", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Competitive intelligence analysis proxy failed" }, { status: 502 });
  }
}
