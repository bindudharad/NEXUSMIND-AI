import { proxyJson } from "@/app/api/boardroom/_proxy";

export const dynamic = "force-dynamic";

export async function GET() {
  return proxyJson("/talent/hidden-leaders/default");
}
