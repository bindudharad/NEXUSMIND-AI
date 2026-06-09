import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/interviews/smart/default");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Smart Interviewer proxy failed" }, { status: 502 });
  }
}
