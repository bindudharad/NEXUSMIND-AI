import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  try {
    return await proxyJson("/living-company-brain/ask", {
      method: "POST",
      body: JSON.stringify(await request.json()),
    });
  } catch (error) {
    return Response.json({ detail: error instanceof Error ? error.message : "Living Company Brain assistant proxy failed" }, { status: 502 });
  }
}
