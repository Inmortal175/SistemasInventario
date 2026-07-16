"use server";

import { revalidatePath } from "next/cache";

import { apiFetch, ApiError } from "@/lib/api";
import { fail, ok, type FormState } from "@/lib/form";
import type {
  ProductionPreparation,
  ProductionResponse,
  ProductionSimulationResponse,
  Recipe,
} from "@/lib/types";

interface RecipeItemInput {
  supply_item_id: string;
  quantity_per_unit: number;
}

export async function createRecipeAction(
  _prev: FormState,
  formData: FormData,
): Promise<FormState> {
  const name = String(formData.get("name") ?? "").trim();
  const description = String(formData.get("description") ?? "").trim();
  const yield_unit = String(formData.get("yield_unit") ?? "UNIT");
  // Si la receta produce un producto terminado, se crea automáticamente (HU-17).
  const makesProduct = formData.get("makes_product") === "on";
  const product_name = makesProduct
    ? String(formData.get("product_name") ?? "").trim() || null
    : null;
  const product_location_id = makesProduct
    ? String(formData.get("product_location_id") ?? "").trim() || null
    : null;
  const shelfRaw = String(formData.get("shelf_life_days") ?? "").trim();
  const shelf_life_days = makesProduct && shelfRaw ? Number(shelfRaw) : null;

  // Los ingredientes llegan como pares repetidos supply_item_id[] / quantity[].
  const supplyIds = formData.getAll("supply_item_id").map(String);
  const quantities = formData.getAll("quantity_per_unit").map(String);

  const items: RecipeItemInput[] = [];
  for (let i = 0; i < supplyIds.length; i++) {
    const sid = supplyIds[i]?.trim();
    const qty = Number(quantities[i]);
    if (sid && qty > 0) {
      items.push({ supply_item_id: sid, quantity_per_unit: qty });
    }
  }

  if (name.length < 2) return fail("El nombre debe tener al menos 2 caracteres.");
  if (items.length === 0) return fail("Agrega al menos un ingrediente válido.");

  try {
    await apiFetch<Recipe>("/recipes", {
      method: "POST",
      body: {
        name,
        description: description || null,
        yield_unit,
        product_name,
        product_location_id,
        shelf_life_days,
        items,
      },
    });
  } catch (err) {
    return fail(err instanceof ApiError ? err.message : "Error al crear la receta.");
  }

  revalidatePath("/production");
  return ok(`Receta "${name}" creada.`);
}

/** Dry-run: no muta stock. Devuelve la simulación serializada en el mensaje. */
export async function simulateProductionAction(
  recipeId: string,
  quantity: number,
): Promise<
  | { status: "ok"; data: ProductionSimulationResponse }
  | { status: "error"; message: string }
> {
  try {
    const data = await apiFetch<ProductionSimulationResponse>(
      "/production/simulate",
      { method: "POST", body: { recipe_id: recipeId, quantity } },
    );
    return { status: "ok", data };
  } catch (err) {
    return {
      status: "error",
      message: err instanceof ApiError ? err.message : "Error en el simulacro.",
    };
  }
}

/** Lista de preparación de una corrida histórica (cómo se fabricó). Solo ADMIN+. */
export async function getPreparationAction(
  productionId: string,
): Promise<
  | { status: "ok"; data: ProductionPreparation }
  | { status: "error"; message: string }
> {
  try {
    const data = await apiFetch<ProductionPreparation>(
      `/production/${productionId}/preparation`,
    );
    return { status: "ok", data };
  } catch (err) {
    return {
      status: "error",
      message: err instanceof ApiError ? err.message : "Error al cargar la preparación.",
    };
  }
}

export async function produceAction(
  recipeId: string,
  quantity: number,
): Promise<
  | { status: "ok"; data: ProductionResponse }
  | { status: "error"; message: string }
> {
  try {
    const data = await apiFetch<ProductionResponse>("/production/produce", {
      method: "POST",
      body: { recipe_id: recipeId, quantity },
    });
    revalidatePath("/supplies");
    revalidatePath("/production");
    return { status: "ok", data };
  } catch (err) {
    return {
      status: "error",
      message: err instanceof ApiError ? err.message : "Error en la producción.",
    };
  }
}
