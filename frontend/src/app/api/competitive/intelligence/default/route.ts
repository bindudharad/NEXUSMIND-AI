import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/competitive/intelligence/default");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Competitive intelligence proxy failed" }, { status: 502 });
  }
}
