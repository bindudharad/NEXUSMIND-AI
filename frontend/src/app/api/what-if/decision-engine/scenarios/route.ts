import { proxyJson } from "@/app/api/boardroom/_proxy";

export async function GET() {
  return proxyJson("/what-if/decision-engine/scenarios");
}

export async function POST(request: Request) {
  return proxyJson("/what-if/decision-engine/scenarios", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
}
