"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type { Category } from "@/lib/types";

export async function createCategoryAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const name = String(formData.get("name") ?? "").trim();
  const color_hex = String(formData.get("color_hex") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const icon_name = String(formData.get("icon_name") ?? "").trim();

  if (name.length < 2) {
    return fail("El nombre debe tener al menos 2 caracteres.");
  }
  if (!/^#[0-9A-Fa-f]{6}$/.test(color_hex)) {
    return fail("El color debe ser hexadecimal, ej. #FF6B9D.");
  }

  try {
    await apiFetch<Category>("/categories", {
      method: "POST",
      body: {
        name,
        color_hex,
        description: description || null,
        icon_name: icon_name || null,
      },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al crear la categoría.");
  }

  revalidatePath("/categories");
  return ok(`Categoría "${name}" creada.`);
}

export async function deactivateCategoryAction(id: string): Promise<void> {
  await apiFetch(`/categories/${id}`, { method: "DELETE" });
  revalidatePath("/categories");
}
