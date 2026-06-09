import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/competitive/intelligence/stream");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Competitive intelligence stream proxy failed";
    return new Response(`event: error\ndata: ${JSON.stringify({ detail: message })}\n\n`, {
      status: 502,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
