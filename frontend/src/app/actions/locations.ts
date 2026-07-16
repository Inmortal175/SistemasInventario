"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type { Location, LocationType } from "@/lib/types";

const LOCATION_CODE_RE = /^(EST|REF|FRZ|CAB|CON|ALM)-\d{2}(-F\d{1,2})?$/;

export async function createLocationAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const code = String(formData.get("code") ?? "").trim().toUpperCase();
  const location_type = String(formData.get("location_type") ?? "") as LocationType;
  const description = String(formData.get("description") ?? "").trim();
  const capacityRaw = String(formData.get("capacity_units") ?? "").trim();

  if (!LOCATION_CODE_RE.test(code)) {
    return fail("Código inválido. Ej: EST-01-F2, REF-02. Solo EST admite sufijo -F.");
  }

  const capacity_units = capacityRaw ? Number(capacityRaw) : null;
  if (capacity_units !== null && (!Number.isInteger(capacity_units) || capacity_units < 1)) {
    return fail("La capacidad debe ser un entero mayor o igual a 1.");
  }

  try {
    await apiFetch<Location>("/locations", {
      method: "POST",
      body: {
        code,
        location_type,
        description: description || null,
        capacity_units,
      },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al crear la ubicación.");
  }

  revalidatePath("/locations");
  return ok(`Ubicación "${code}" creada.`);
}

export async function deactivateLocationAction(id: string): Promise<void> {
  await apiFetch(`/locations/${id}`, { method: "DELETE" });
  revalidatePath("/locations");
}
