import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/workflows/autonomous/stream");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Autonomous Workflow stream failed" }, { status: 502 });
  }
}
