"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import { updateSessionName } from "@/lib/session";
import type { User } from "@/lib/types";

export async function updateProfileAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const full_name = String(formData.get("full_name") ?? "").trim();
  if (full_name.length < 2) {
    return fail("El nombre debe tener al menos 2 caracteres.");
  }
  try {
    await apiFetch<User>("/auth/me", {
      method: "PATCH",
      body: { full_name },
    });
    // Refresca el nombre en la cookie de sesión para que el sidebar lo muestre.
    await updateSessionName(full_name);
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al actualizar el perfil.");
  }
  revalidatePath("/profile");
  return ok("Perfil actualizado.");
}

export async function changePasswordAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const current_password = String(formData.get("current_password") ?? "");
  const new_password = String(formData.get("new_password") ?? "");
  const confirm = String(formData.get("confirm_password") ?? "");

  if (new_password.length < 8) {
    return fail("La nueva contraseña debe tener al menos 8 caracteres.");
  }
  if (new_password !== confirm) {
    return fail("La confirmación no coincide con la nueva contraseña.");
  }
  try {
    await apiFetch<User>("/auth/me/password", {
      method: "PATCH",
      body: { current_password, new_password },
    });
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      return fail("La contraseña actual es incorrecta.");
    }
    return fail(err instanceof ApiError ? err.message : "Error al cambiar la contraseña.");
  }
  return ok("Contraseña actualizada.");
}
