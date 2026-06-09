import { proxyJson } from "../_proxy";

export async function POST(request: Request) {
  const payload = await request.json();
  return proxyJson("/boardroom/assistant", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
