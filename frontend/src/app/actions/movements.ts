"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type { MovementResponse, MovementType } from "@/lib/types";

export async function registerMovementAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const supply_item_id = String(formData.get("supply_item_id") ?? "").trim();
  const movement_type = String(formData.get("movement_type") ?? "") as MovementType;
  const quantity = String(formData.get("quantity") ?? "").trim();
  const notes = String(formData.get("notes") ?? "").trim();

  if (!supply_item_id) return fail("Selecciona un insumo.");
  if (!movement_type) return fail("Selecciona el tipo de movimiento.");
  if (!quantity || Number(quantity) <= 0) {
    return fail("La cantidad debe ser mayor a 0.");
  }

  try {
    const result = await apiFetch<MovementResponse>("/movements", {
      method: "POST",
      body: {
        supply_item_id,
        movement_type,
        quantity,
        notes: notes || null,
      },
    });
    revalidatePath("/supplies");
    revalidatePath("/dashboard");
    return ok(
      result.alert_triggered
        ? `Movimiento registrado. Stock: ${result.stock_after}. ⚠️ Stock bajo el mínimo.`
        : `Movimiento registrado. Stock actual: ${result.stock_after}.`,
    );
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al registrar el movimiento.");
  }
}
