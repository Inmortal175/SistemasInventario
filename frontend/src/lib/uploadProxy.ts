import "server-only";

import { NextRequest, NextResponse } from "next/server";

import { getToken } from "./session";

const DEFAULT_API_URL = "http://localhost:8000/api/v1";

function baseUrl(): string {
  return (
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    DEFAULT_API_URL
  );
}

/** Reenvía un multipart al backend adjuntando el Bearer. Existe porque el token
 *  vive en una cookie httpOnly: el navegador no puede llamar al backend directo. */
export async function proxyUpload(
  request: NextRequest,
  path: string,
): Promise<{ response: NextResponse; data: unknown; ok: boolean }> {
  const token = await getToken();
  if (!token) {
    return {
      ok: false,
      data: null,
      response: NextResponse.json({ error: "No autenticado" }, { status: 401 }),
    };
  }

  const form = await request.formData();
  const res = await fetch(`${baseUrl()}${path}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: form,
    cache: "no-store",
  });

  const data = await res.json().catch(() => ({}));
  return {
    ok: res.ok,
    data,
    response: NextResponse.json(data, { status: res.status }),
  };
}
