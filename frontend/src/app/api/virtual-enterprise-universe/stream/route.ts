import { proxyStream } from "@/app/api/boardroom/_proxy";

export async function GET() {
  return proxyStream("/virtual-enterprise-universe/stream");
}
