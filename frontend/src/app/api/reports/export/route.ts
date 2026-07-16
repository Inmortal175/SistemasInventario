import { NextRequest, NextResponse } from "next/server";

import { getToken } from "@/lib/session";

const DEFAULT_API_URL = "http://localhost:8000/api/v1";

function baseUrl(): string {
  return (
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    DEFAULT_API_URL
  );
}

// Proxy autenticado: el token vive en una cookie httpOnly, así que el navegador
// no puede llamar al backend directamente. Este handler adjunta el Bearer y
// reenvía el CSV como descarga (HU-12).
export async function GET(request: NextRequest) {
  const token = await getToken();
  if (!token) {
    return NextResponse.json({ error: "No autenticado" }, { status: 401 });
  }

  const startDate = request.nextUrl.searchParams.get("start_date");
  const qs = new URLSearchParams({ format: "csv" });
  if (startDate) qs.set("start_date", startDate);

  const res = await fetch(`${baseUrl()}/reports/export?${qs.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!res.ok) {
    return NextResponse.json(
      { error: "No se pudo generar el reporte" },
      { status: res.status },
    );
  }

  const body = await res.text();
  return new NextResponse(body, {
    status: 200,
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition":
        "attachment; filename=inventory_olap_export.csv",
    },
  });
}
