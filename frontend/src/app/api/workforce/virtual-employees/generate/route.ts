import { proxyJson } from "@/app/api/workforce/virtual-employees/_proxy";

export async function POST(request: Request) {
  return proxyJson("/workforce/virtual-employees/generate", {
    method: "POST",
    body: JSON.stringify(await request.json()),
  });
}
