import { proxyJson } from "@/app/api/boardroom/_proxy";

export async function GET() {
  return proxyJson("/strategic/decision-engine/default");
}
