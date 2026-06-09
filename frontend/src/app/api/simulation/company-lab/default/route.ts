import { proxyJson } from "../_proxy";

export async function GET() {
  try {
    return await proxyJson("/simulation/company-lab/default");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Company Simulation Lab proxy failed" }, { status: 502 });
  }
}
