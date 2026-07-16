"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";

export async function createBatchAction(
  supplyId: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const quantity = Number(formData.get("quantity"));
  const batch_code = String(formData.get("batch_code") ?? "").trim();
  const expiration_date = String(formData.get("expiration_date") ?? "").trim();
  const unit_cost = Number(formData.get("unit_cost") ?? 0);
  const vendor_name = String(formData.get("vendor_name") ?? "").trim();

  if (!(quantity > 0)) return fail("La cantidad debe ser mayor que 0.");
  if (batch_code.length < 1) return fail("El código de lote es obligatorio.");

  try {
    await apiFetch(`/supplies/${supplyId}/batches`, {
      method: "POST",
      body: {
        quantity,
        batch_code,
        expiration_date: expiration_date || null,
        unit_cost: unit_cost || 0,
        vendor_name: vendor_name || null,
      },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al registrar el lote.");
  }

  revalidatePath(`/supplies/${supplyId}`);
  revalidatePath("/supplies");
  return ok(`Lote "${batch_code}" registrado.`);
}

export async function consumeFifoAction(
  supplyId: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const quantity = Number(formData.get("quantity"));
  const movement_type = String(formData.get("movement_type") ?? "EXIT");
  const notes = String(formData.get("notes") ?? "").trim();

  if (!(quantity > 0)) return fail("La cantidad debe ser mayor que 0.");

  try {
    await apiFetch(`/supplies/${supplyId}/batches/consume`, {
      method: "POST",
      body: {
        supply_item_id: supplyId,
        movement_type,
        quantity,
        notes: notes || null,
      },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al consumir (FIFO).");
  }

  revalidatePath(`/supplies/${supplyId}`);
  revalidatePath("/supplies");
  return ok("Consumo FIFO registrado.");
}

export async function reconcileAction(
  supplyId: string,
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const physical_stock = Number(formData.get("physical_stock"));
  const reason = String(formData.get("reason") ?? "").trim();

  if (Number.isNaN(physical_stock) || physical_stock < 0) {
    return fail("El stock físico debe ser un número ≥ 0.");
  }
  if (reason.length < 3) return fail("Indica el motivo del ajuste (mín. 3 caracteres).");

  try {
    await apiFetch(`/supplies/reconciliation`, {
      method: "POST",
      body: { supply_id: supplyId, physical_stock, reason },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error en la conciliación.");
  }

  revalidatePath(`/supplies/${supplyId}`);
  revalidatePath("/supplies");
  return ok("Conciliación aplicada.");
}
