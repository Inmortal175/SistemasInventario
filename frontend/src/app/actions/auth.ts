"use server";

import { redirect } from "next/navigation";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, type FormState } from "@/lib/form";
import { createSession, destroySession } from "@/lib/session";
import type { TokenResponse } from "@/lib/types";

export async function loginAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!email || !password) {
    return fail("Ingresa tu correo y contraseña.");
  }

  try {
    const token = await apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      auth: false,
      form: true,
      body: { username: email, password },
    });
    await createSession(token);
  } catch (err) {
    if (err instanceof ApiError) {
      return fail(
        err.status === 401
          ? "Correo o contraseña incorrectos."
          : err.message,
      );
    }
    return fail("No se pudo conectar con el servidor.");
  }

  // Fuera del try: redirect() lanza una señal que no debe capturarse arriba.
  redirect("/dashboard");
}

export async function logoutAction(): Promise<void> {
  await destroySession();
  redirect("/login");
}
