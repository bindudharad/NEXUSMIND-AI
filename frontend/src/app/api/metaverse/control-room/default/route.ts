import { proxyJson } from "../_proxy";

export async function GET() {
  return proxyJson("/metaverse/control-room/default");
}
