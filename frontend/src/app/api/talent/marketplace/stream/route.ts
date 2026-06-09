import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/talent/marketplace/stream");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Talent marketplace stream proxy failed" }, { status: 502 });
  }
}
