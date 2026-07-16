"use client";

import { Fragment, useState, useTransition } from "react";

import { Icon } from "@/components/Icon";
import { produceAction, simulateProductionAction } from "@/app/actions/production";
import type { FormatConfig } from "@/lib/format";
import { formatDate, formatQuantity, formatQuantityUnit } from "@/lib/labels";
import type {
  ProductionResponse,
  ProductionSimulationResponse,
  Recipe,
} from "@/lib/types";

// Componente de cliente: el locale llega como prop porque los ajustes solo se
// leen en el servidor.
export function ProduceWidget({
  recipes,
  fmt,
}: {
  recipes: Recipe[];
  fmt: FormatConfig;
}) {
  const [recipeId, setRecipeId] = useState(recipes[0]?.id ?? "");
  const [quantity, setQuantity] = useState(1);
  const [sim, setSim] = useState<ProductionSimulationResponse | null>(null);
  const [done, setDone] = useState<ProductionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  // Cualquier cambio invalida el simulacro previo: hay que volver a simular.
  function reset() {
    setSim(null);
    setDone(null);
    setError(null);
  }

  function handleSimulate() {
    if (!recipeId || quantity < 1) return;
    setError(null);
    setDone(null);
    startTransition(async () => {
      const res = await simulateProductionAction(recipeId, quantity);
      if (res.status === "ok") setSim(res.data);
      else setError(res.message);
    });
  }

  function handleProduce() {
    if (!sim?.feasible) return;
    startTransition(async () => {
      const res = await produceAction(recipeId, quantity);
      if (res.status === "ok") {
        setDone(res.data);
        setSim(null);
      } else {
        setError(res.message);
      }
    });
  }

  return (
    <div className="card space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="sm:col-span-2">
          <label htmlFor="recipe" className="label">Receta</label>
          <select
            id="recipe"
            className="input"
            value={recipeId}
            onChange={(e) => {
              setRecipeId(e.target.value);
              reset();
            }}
          >
            {recipes.map((r) => (
              <option key={r.id} value={r.id}>{r.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="qty" className="label">Unidades</label>
          <input
            id="qty"
            type="number"
            min={1}
            className="input"
            value={quantity}
            onChange={(e) => {
              setQuantity(Math.max(1, Number(e.target.value)));
              reset();
            }}
          />
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="btn-ghost"
          onClick={handleSimulate}
          disabled={pending || !recipeId}
        >
          <Icon name="reconcile" /> Simular stock
        </button>
        <button
          type="button"
          className="btn-primary"
          onClick={handleProduce}
          disabled={pending || !sim?.feasible}
        >
          <Icon name="production" /> Producir
        </button>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      {done && (
        <div className="rounded-lg bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <p className="flex items-center gap-2 font-semibold">
            <Icon name="ok" /> Producción registrada: {done.quantity_produced} unidad(es)
          </p>
          <ul className="mt-2 space-y-1">
            {done.ingredients.map((ing) => (
              <li key={ing.supply_id} className="flex justify-between">
                <span>{ing.supply_name}</span>
                <span>−{formatQuantity(ing.consumed, fmt)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sim && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            sim.feasible
              ? "border-emerald-200 bg-emerald-50"
              : "border-red-200 bg-red-50"
          }`}
        >
          <p
            className={`flex items-center gap-2 font-semibold ${
              sim.feasible ? "text-emerald-800" : "text-red-700"
            }`}
          >
            <Icon name={sim.feasible ? "ok" : "alert"} />
            {sim.feasible
              ? `Simulacro OK: hay stock para ${sim.quantity} unidad(es)`
              : "Simulacro: falta stock de algún ingrediente"}
          </p>
          <p className="mt-3 mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Lista de preparación
          </p>
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-slate-400">
                <th className="pb-1 font-medium">Ingrediente</th>
                <th className="pb-1 font-medium">Ubicación</th>
                <th className="pb-1 text-right font-medium">Requerido</th>
                <th className="pb-1 text-right font-medium">Disponible</th>
                <th className="pb-1 text-right font-medium">Déficit</th>
              </tr>
            </thead>
            <tbody>
              {sim.ingredients.map((ing) => (
                <Fragment key={ing.supply_id}>
                  <tr className={ing.sufficient ? "text-slate-600" : "text-red-600"}>
                    <td className="py-0.5">{ing.supply_name}</td>
                    <td className="py-0.5">
                      {ing.location_code ? (
                        <span className="inline-flex items-center gap-1 font-medium">
                          <Icon name="locations" /> {ing.location_code}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="py-0.5 text-right">{formatQuantityUnit(ing.required, ing.unit, fmt)}</td>
                    <td className="py-0.5 text-right">{formatQuantityUnit(ing.available, ing.unit, fmt)}</td>
                    <td className="py-0.5 text-right font-medium">
                      {Number(ing.deficit) > 0 ? formatQuantityUnit(ing.deficit, ing.unit, fmt) : "—"}
                    </td>
                  </tr>
                  {ing.batch_plan.length > 0 && (
                    <tr>
                      <td colSpan={5} className="pb-1.5 pl-3 text-[11px] text-slate-500">
                        <span className="font-medium">Extraer de: </span>
                        {ing.batch_plan
                          .map(
                            (p) =>
                              `${p.batch_code} −${formatQuantityUnit(p.take, ing.unit, fmt)}` +
                              (p.expiration_date ? ` (vence ${formatDate(p.expiration_date)})` : ""),
                          )
                          .join("  ·  ")}
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
          <p className="mt-2 text-[11px] text-slate-400">
            El simulacro no descuenta stock. Confirma con “Producir” para aplicar el
            descuento FIFO de forma atómica.
          </p>
        </div>
      )}
    </div>
  );
}
