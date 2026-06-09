import { proxyJson } from "@/app/api/boardroom/_proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return proxyJson("/global-risk/scanner/scan", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
}
