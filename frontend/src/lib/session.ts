import "server-only";

import { cookies } from "next/headers";

import type { TokenResponse, UserRole } from "./types";

const TOKEN_COOKIE = "pastry_token";
const USER_COOKIE = "pastry_user";

export interface SessionUser {
  id: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string | null;
}

export async function createSession(token: TokenResponse): Promise<void> {
  const store = await cookies();
  const maxAge = token.expires_in * 60; // expires_in viene en minutos

  const common = {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge,
  };

  store.set(TOKEN_COOKIE, token.access_token, common);
  store.set(
    USER_COOKIE,
    JSON.stringify({
      id: token.user_id,
      full_name: token.full_name,
      role: token.role,
      avatar_url: token.avatar_url,
    } satisfies SessionUser),
    common,
  );
}

async function patchSessionUser(patch: Partial<SessionUser>): Promise<void> {
  const store = await cookies();
  const raw = store.get(USER_COOKIE)?.value;
  if (!raw) return;
  try {
    const user = JSON.parse(raw) as SessionUser;
    store.set(USER_COOKIE, JSON.stringify({ ...user, ...patch } satisfies SessionUser), {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
    });
  } catch {
    // cookie corrupta: se ignora, el próximo login la regenera
  }
}

export async function updateSessionName(fullName: string): Promise<void> {
  await patchSessionUser({ full_name: fullName });
}

/** El menú lee el avatar de la cookie, no de la API: sin esto la foto recién
 *  subida no aparecería hasta el siguiente inicio de sesión. */
export async function updateSessionAvatar(avatarUrl: string | null): Promise<void> {
  await patchSessionUser({ avatar_url: avatarUrl });
}

export async function destroySession(): Promise<void> {
  const store = await cookies();
  store.delete(TOKEN_COOKIE);
  store.delete(USER_COOKIE);
}

export async function getToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(TOKEN_COOKIE)?.value ?? null;
}

export async function getSessionUser(): Promise<SessionUser | null> {
  const store = await cookies();
  const raw = store.get(USER_COOKIE)?.value;
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SessionUser;
  } catch {
    return null;
  }
}
