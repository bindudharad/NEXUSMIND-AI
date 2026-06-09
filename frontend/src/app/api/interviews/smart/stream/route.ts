import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/interviews/smart/stream");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Smart Interviewer stream proxy failed" }, { status: 502 });
  }
}
