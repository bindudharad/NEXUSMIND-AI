import { proxyStream } from "@/app/api/boardroom/_proxy";

export const dynamic = "force-dynamic";

export async function GET() {
  return proxyStream("/talent/hidden-leaders/stream");
}
