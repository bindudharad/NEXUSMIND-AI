import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    return await proxyJson("/workflows/autonomous/run", {
      method: "POST",
      body: JSON.stringify(await request.json()),
    });
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Autonomous Workflow run proxy failed" }, { status: 502 });
  }
}
