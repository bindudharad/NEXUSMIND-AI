import { proxyJson } from "@/app/api/workforce/virtual-employees/_proxy";

export async function GET() {
  return proxyJson("/workforce/virtual-employees/default");
}
