import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    return await proxyJson("/talent/marketplace/analyze", {
      method: "POST",
      body: JSON.stringify(await request.json()),
    });
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Talent marketplace analysis proxy failed" }, { status: 502 });
  }
}
