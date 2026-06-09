import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/business/prediction/stream");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Business Prediction stream failed" }, { status: 502 });
  }
}
