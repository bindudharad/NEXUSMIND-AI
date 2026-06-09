import { proxyJson } from "../_proxy";

export async function GET() {
  return proxyJson("/agents/workforce/default");
}
