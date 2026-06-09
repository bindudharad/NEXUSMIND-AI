import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/workflows/autonomous/default");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Autonomous Workflow proxy failed" }, { status: 502 });
  }
}
