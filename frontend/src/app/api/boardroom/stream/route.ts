import { proxyStream } from "../_proxy";

export async function GET() {
  return proxyStream("/boardroom/stream");
}
