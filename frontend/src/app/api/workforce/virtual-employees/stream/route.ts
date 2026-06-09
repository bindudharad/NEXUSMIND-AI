import { proxyStream } from "@/app/api/workforce/virtual-employees/_proxy";

export async function GET() {
  return proxyStream("/workforce/virtual-employees/stream");
}
