import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/emotion/map/stream");
  } catch {
    return new Response("event: error\ndata: {\"detail\":\"Company emotion map stream failed\"}\n\n", {
      status: 500,
      headers: { "Content-Type": "text/event-stream" },
    });
  }
}
