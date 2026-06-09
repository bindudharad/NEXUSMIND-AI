import { proxyStream } from "@/app/api/boardroom/_proxy";

export const dynamic = "force-dynamic";

export async function GET() {
  return proxyStream("/global-risk/scanner/stream");
}
