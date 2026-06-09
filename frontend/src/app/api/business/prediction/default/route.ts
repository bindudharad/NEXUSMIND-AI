import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/business/prediction/default");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Business Prediction proxy failed" }, { status: 502 });
  }
}
