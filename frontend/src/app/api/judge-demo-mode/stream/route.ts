import { proxyStream } from "@/app/api/boardroom/_proxy";

export async function GET() {
  return proxyStream("/judge-demo-mode/stream");
}
