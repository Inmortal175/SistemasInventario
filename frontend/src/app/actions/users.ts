"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type { User } from "@/lib/types";

export async function createUserAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const email = String(formData.get("email") ?? "").trim();
  const full_name = String(formData.get("full_name") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  const role = String(formData.get("role") ?? "STAFF");

  if (!email.includes("@")) return fail("Email inválido.");
  if (full_name.length < 2) return fail("El nombre debe tener al menos 2 caracteres.");
  if (password.length < 8) return fail("La contraseña debe tener al menos 8 caracteres.");

  try {
    await apiFetch<User>("/users", {
      method: "POST",
      body: { email, full_name, password, role },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al crear el usuario.");
  }

  revalidatePath("/users");
  return ok(`Usuario "${email}" creado como ${role}.`);
}

export async function resetPasswordAction(
  id: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const new_password = String(formData.get("new_password") ?? "");
  if (new_password.length < 8) {
    return fail("La contraseña debe tener al menos 8 caracteres.");
  }
  try {
    await apiFetch(`/users/${id}/password`, {
      method: "PATCH",
      body: { new_password },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al restablecer.");
  }
  revalidatePath("/users");
  return ok("Contraseña restablecida. El usuario debe iniciar sesión de nuevo.");
}

export async function suspendUserAction(id: string): Promise<void> {
  await apiFetch(`/users/${id}/suspend`, { method: "PATCH" });
  revalidatePath("/users");
}

export async function reactivateUserAction(id: string): Promise<void> {
  await apiFetch(`/users/${id}/reactivate`, { method: "PATCH" });
  revalidatePath("/users");
}
