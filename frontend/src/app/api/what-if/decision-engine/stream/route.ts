import { proxyStream } from "@/app/api/boardroom/_proxy";

export async function GET() {
  return proxyStream("/what-if/decision-engine/stream");
}
