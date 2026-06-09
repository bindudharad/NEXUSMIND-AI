import { proxyJson } from "@/app/api/boardroom/_proxy";

export async function POST(request: Request) {
  return proxyJson("/shadow-company/assistant", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
}
