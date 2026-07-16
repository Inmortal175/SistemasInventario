import { NextRequest } from "next/server";

import { updateSessionAvatar } from "@/lib/session";
import { proxyUpload } from "@/lib/uploadProxy";

export async function POST(request: NextRequest) {
  const { response, data, ok } = await proxyUpload(request, "/auth/me/avatar");

  // El menú lee el avatar de la cookie de sesión, no de la API: sin refrescarla
  // aquí, la foto recién subida no se vería hasta el siguiente login.
  const avatarUrl = (data as { avatar_url?: unknown } | null)?.avatar_url;
  if (ok && typeof avatarUrl === "string") {
    await updateSessionAvatar(avatarUrl);
  }

  return response;
}
