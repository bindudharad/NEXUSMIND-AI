import { proxyJson } from "@/app/api/boardroom/_proxy";

export const dynamic = "force-dynamic";

export async function GET() {
  return proxyJson("/global-risk/scanner/default");
}
