import { proxyStream } from "../_proxy";

export async function GET() {
  return proxyStream("/metaverse/control-room/stream");
}
