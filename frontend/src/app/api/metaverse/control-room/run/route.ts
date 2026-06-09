import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  return proxyJson("/metaverse/control-room/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await request.text(),
  });
}
