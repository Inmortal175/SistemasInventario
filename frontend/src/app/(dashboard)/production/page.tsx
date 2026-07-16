import { PageHeader } from "@/components/PageHeader";
import { Icon } from "@/components/Icon";
import { InfoBanner } from "@/components/InfoBanner";
import { formatConfig, formatMoney } from "@/lib/format";
import {
  formatDateTime,
  formatQuantity,
  formatQuantityUnit,
  isAdmin,
  UNIT_LABELS,
} from "@/lib/labels";
import type { UnitMeasure } from "@/lib/types";
import {
  getLocations,
  getProductionHistory,
  getRecipes,
  getSettings,
  getSupplies,
} from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { PreparationButton } from "./PreparationButton";
import { ProduceWidget } from "./ProduceWidget";
import { RecipeForm } from "./RecipeForm";

export default async function ProductionPage() {
  const [recipes, supplies, products, locations, user, settings] = await Promise.all([
    getRecipes(),
    getSupplies({ limit: 100, item_type: "INGREDIENT" }),
    getSupplies({ limit: 100, item_type: "FINISHED_PRODUCT" }),
    getLocations(),
    getSessionUser(),
    getSettings(),
  ]);
  const fmt = formatConfig(settings);
  const canViewHistory = user ? isAdmin(user.role) : false;
  // El historial es solo ADMIN+; evita un 403 pidiéndolo únicamente si corresponde.
  const history = canViewHistory
    ? await getProductionHistory(1, 20).catch(() => null)
    : null;

  // Nombres de insumos y productos para pintar recetas.
  const supplyName = new Map(
    [...supplies.items, ...products.items].map((s) => [s.id, s.name]),
  );
  const supplyUnit = new Map<string, UnitMeasure>(
    [...supplies.items, ...products.items].map((s) => [s.id, s.unit_of_measure]),
  );
  const supplyOptions = supplies.items.map((s) => ({
    id: s.id,
    label: `${s.name} (${UNIT_LABELS[s.unit_of_measure]})`,
  }));
  // Ubicaciones donde guardar el producto (se priorizan refrigeradoras/congeladoras).
  const locationOptions = locations.items
    .filter((l) => l.is_active)
    .map((l) => ({ id: l.id, label: l.code }));
  const canCreate = user ? isAdmin(user.role) : false;

  return (
    <>
      <PageHeader
        title="Producción"
        subtitle="Descuento automático de insumos por receta (BOM) con simulacro previo"
      />

      <InfoBanner>
        Define recetas (qué insumos y cuánto lleva cada producto). Al producir, primero
        pulsa <strong>Simular stock</strong> para ver si alcanzan los ingredientes; si es
        viable, <strong>Producir</strong> descuenta todo por FIFO en una sola transacción
        (si falta un ingrediente, no descuenta nada).
      </InfoBanner>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-800">
            <Icon name="production" className="text-brand-500" /> Producir
          </h2>
          {recipes.items.length === 0 ? (
            <div className="card text-sm text-slate-500">
              Aún no hay recetas. {canCreate ? "Crea una a la derecha." : "Pide a un administrador que registre recetas."}
            </div>
          ) : (
            <ProduceWidget recipes={recipes.items} fmt={fmt} />
          )}

          <h2 className="mb-3 mt-8 flex items-center gap-2 text-lg font-semibold text-slate-800">
            <Icon name="recipes" className="text-brand-500" /> Recetas
          </h2>
          <div className="space-y-3">
            {recipes.items.map((r) => (
              <div key={r.id} className="card">
                <p className="font-semibold text-slate-800">{r.name}</p>
                {r.description && (
                  <p className="mt-0.5 text-sm text-slate-500">{r.description}</p>
                )}
                {r.produces_supply_item_id && (
                  <p className="mt-1 inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                    <Icon name="production" /> Produce:{" "}
                    {supplyName.get(r.produces_supply_item_id) ?? "producto"}
                    {r.shelf_life_days != null && ` · dura ${r.shelf_life_days} d`}
                  </p>
                )}
                <ul className="mt-2 space-y-1 text-sm text-slate-600">
                  {r.items.map((it) => (
                    <li key={it.supply_item_id} className="flex justify-between">
                      <span>{supplyName.get(it.supply_item_id) ?? "insumo"}</span>
                      <span className="text-slate-400">
                        {formatQuantityUnit(
                          it.quantity_per_unit,
                          supplyUnit.get(it.supply_item_id) ?? "UNIT",
                          fmt,
                        )}{" "}
                        / unidad
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        {canCreate && (
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-800">
              <Icon name="add" className="text-brand-500" /> Nueva receta
            </h2>
            <div className="card">
              <RecipeForm supplies={supplyOptions} locations={locationOptions} />
            </div>
          </section>
        )}
      </div>

      {canViewHistory && (
        <section className="mt-8">
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-800">
            <Icon name="production" className="text-brand-500" /> Historial de producción
          </h2>
          {!history || history.items.length === 0 ? (
            <div className="card text-sm text-slate-500">
              Aún no se ha registrado ninguna producción.
            </div>
          ) : (
            <div className="card overflow-x-auto p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                    <th className="px-4 py-3">Fecha</th>
                    <th className="px-4 py-3">Receta</th>
                    <th className="px-4 py-3">Producto</th>
                    <th className="px-4 py-3 text-right">Cantidad</th>
                    <th className="px-4 py-3 text-right">Costo insumos</th>
                    <th className="px-4 py-3">Responsable</th>
                    <th className="px-4 py-3 text-right">Preparación</th>
                  </tr>
                </thead>
                <tbody>
                  {history.items.map((run) => (
                    <tr key={run.production_id} className="border-b border-slate-50">
                      <td className="whitespace-nowrap px-4 py-3 text-slate-500">
                        {formatDateTime(run.created_at)}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-800">{run.recipe_name}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {run.product_name ?? "—"}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700">
                        {formatQuantity(run.quantity_produced, fmt)}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-700">
                        {formatMoney(run.total_ingredient_cost, fmt)}
                      </td>
                      <td className="px-4 py-3 text-slate-500">{run.performed_by_email}</td>
                      <td className="px-4 py-3 text-right">
                        <PreparationButton productionId={run.production_id} fmt={fmt} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </>
  );
}
