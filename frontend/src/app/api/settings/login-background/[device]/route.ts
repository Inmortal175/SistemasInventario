import { NextRequest, NextResponse } from "next/server";

import { proxyUpload } from "@/lib/uploadProxy";

const DEVICES = new Set(["mobile", "tablet", "desktop"]);

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ device: string }> },
) {
  const { device } = await params;
  // El segmento viene de la URL: sin esta guarda se reenviaría cualquier cosa
  // al backend como parte de la ruta.
  if (!DEVICES.has(device)) {
    return NextResponse.json({ detail: "Dispositivo no válido." }, { status: 400 });
  }

  const { response } = await proxyUpload(request, `/settings/login-background/${device}`);
  return response;
}
