import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    return await proxyJson("/business/prediction/ask", {
      method: "POST",
      body: JSON.stringify(await request.json()),
    });
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Business assistant proxy failed" }, { status: 502 });
  }
}
