import { proxyJson } from "@/app/api/boardroom/_proxy";

export async function GET() {
  return proxyJson("/what-if/decision-engine/default");
}
