import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/knowledge/brain/stream");
  } catch {
    return new Response("event: error\ndata: {\"detail\":\"Company Brain stream failed\"}\n\n", {
      status: 500,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
