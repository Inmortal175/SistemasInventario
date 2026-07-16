import { NextRequest } from "next/server";

import { proxyUpload } from "@/lib/uploadProxy";

export async function POST(request: NextRequest) {
  const { response } = await proxyUpload(request, "/settings/logo");
  return response;
}
