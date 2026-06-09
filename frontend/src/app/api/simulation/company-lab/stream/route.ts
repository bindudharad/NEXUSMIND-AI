import { proxyStream } from "../_proxy";

export async function GET() {
  try {
    return await proxyStream("/simulation/company-lab/stream");
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Company Simulation Lab stream failed" }, { status: 502 });
  }
}
