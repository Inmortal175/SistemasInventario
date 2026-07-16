"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type { LoginBackgroundDevice, SystemSettings, ThemeName } from "@/lib/types";

const THEMES: ThemeName[] = ["rosa", "chocolate", "menta", "azul"];

// El nombre, el tema y la moneda viven en el layout raíz y en cada listado: sin
// revalidar la raíz completa, seguirían mostrándose los valores anteriores.
function revalidateBranding(): void {
  revalidatePath("/", "layout");
}

async function patchSettings(body: Record<string, unknown>): Promise<FormState> {
  try {
    await apiFetch<SystemSettings>("/settings", { method: "PATCH", body });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al guardar los ajustes.");
  }
  revalidateBranding();
  return ok("Ajustes guardados.");
}

export async function updateBrandingAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const app_name = String(formData.get("app_name") ?? "").trim();
  const theme = String(formData.get("theme") ?? "") as ThemeName;
  const login_overlay_opacity = Number(formData.get("login_overlay_opacity") ?? 40);

  if (app_name.length < 2 || app_name.length > 80) {
    return fail("El nombre debe tener entre 2 y 80 caracteres.");
  }
  if (!THEMES.includes(theme)) {
    return fail("Tema no válido.");
  }
  if (login_overlay_opacity < 0 || login_overlay_opacity > 80) {
    return fail("La opacidad del velo debe estar entre 0 % y 80 %.");
  }

  return patchSettings({ app_name, theme, login_overlay_opacity });
}

export async function updateOperationAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const expiration_alert_days = Number(formData.get("expiration_alert_days") ?? 5);
  const page_size = Number(formData.get("page_size") ?? 15);
  const currency_code = String(formData.get("currency_code") ?? "").trim().toUpperCase();
  const locale = String(formData.get("locale") ?? "").trim();

  if (!Number.isInteger(expiration_alert_days) || expiration_alert_days < 1 || expiration_alert_days > 90) {
    return fail("El aviso de vencimiento debe estar entre 1 y 90 días.");
  }
  if (!Number.isInteger(page_size) || page_size < 5 || page_size > 100) {
    return fail("El tamaño de página debe estar entre 5 y 100.");
  }
  if (!/^[A-Z]{3}$/.test(currency_code)) {
    return fail("La moneda debe ser un código ISO de 3 letras, ej. PEN.");
  }
  if (!/^[a-z]{2}(-[A-Z]{2})?$/.test(locale)) {
    return fail("El formato regional debe ser tipo es-PE o es.");
  }

  return patchSettings({ expiration_alert_days, page_size, currency_code, locale });
}

export async function updateBusinessAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  // Cadena vacía = borrar el campo. La API lo interpreta así a propósito.
  const business_name = String(formData.get("business_name") ?? "").trim();
  const tax_id = String(formData.get("tax_id") ?? "").trim();
  const address = String(formData.get("address") ?? "").trim();
  const phone = String(formData.get("phone") ?? "").trim();

  if (business_name.length > 150) return fail("La razón social es demasiado larga.");
  if (tax_id.length > 20) return fail("El RUC es demasiado largo.");

  return patchSettings({ business_name, tax_id, address, phone });
}

export async function removeLogoAction(): Promise<void> {
  await apiFetch("/settings/logo", { method: "DELETE" });
  revalidateBranding();
}

export async function removeLoginBackgroundAction(
  device: LoginBackgroundDevice,
): Promise<void> {
  await apiFetch(`/settings/login-background/${device}`, { method: "DELETE" });
  revalidateBranding();
}
