import { proxyJson } from "@/app/api/boardroom/_proxy";

export async function POST(request: Request) {
  return proxyJson("/time-machine/ask", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
}
