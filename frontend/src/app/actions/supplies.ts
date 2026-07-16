"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type { SupplyItem, UnitMeasure } from "@/lib/types";

export async function createSupplyAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const get = (k: string) => String(formData.get(k) ?? "").trim();

  const name = get("name");
  const sku = get("sku");
  const category_id = get("category_id");
  const location_id = get("location_id");
  const unit_of_measure = get("unit_of_measure") as UnitMeasure;

  if (name.length < 2) return fail("El nombre debe tener al menos 2 caracteres.");
  if (sku.length < 2) return fail("El SKU debe tener al menos 2 caracteres.");
  if (!category_id) return fail("Selecciona una categoría.");
  if (!location_id) return fail("Selecciona una ubicación.");

  const current_stock = get("current_stock") || "0";
  const minimum_stock = get("minimum_stock") || "0";
  const maximum_stock = get("maximum_stock") || "0";
  const unit_cost = get("unit_cost") || "0";

  if (Number(minimum_stock) > Number(maximum_stock)) {
    return fail("El stock mínimo no puede superar al máximo.");
  }

  const is_perishable = formData.get("is_perishable") === "on";
  const expiration_date = get("expiration_date") || null;
  const supplier_name = get("supplier_name") || null;
  const description = get("description") || null;

  try {
    await apiFetch<SupplyItem>("/supplies", {
      method: "POST",
      body: {
        name,
        sku,
        description,
        category_id,
        location_id,
        unit_of_measure,
        current_stock,
        minimum_stock,
        maximum_stock,
        unit_cost,
        is_perishable,
        expiration_date,
        supplier_name,
      },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al crear el insumo.");
  }

  revalidatePath("/supplies");
  return ok(`Insumo "${name}" registrado.`);
}
