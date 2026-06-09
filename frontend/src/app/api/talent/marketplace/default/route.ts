import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/talent/marketplace/default");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Talent marketplace proxy failed" }, { status: 502 });
  }
}
