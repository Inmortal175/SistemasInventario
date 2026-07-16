"use client";

import { useState, useTransition } from "react";

import { Icon } from "@/components/Icon";
import { getPreparationAction } from "@/app/actions/production";
import type { FormatConfig } from "@/lib/format";
import { formatDate, formatDateTime, formatMoney, formatQuantityUnit } from "@/lib/labels";
import type { ProductionPreparation } from "@/lib/types";

// Botón por fila del historial: abre un modal con la lista de preparación que se
// usó para fabricar esa corrida (snapshot inmutable: insumo, cantidad, unidad,
// ubicación y lotes de donde salió).
export function PreparationButton({
  productionId,
  fmt,
}: {
  productionId: string;
  fmt: FormatConfig;
}) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<ProductionPreparation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function handleOpen() {
    setOpen(true);
    setError(null);
    if (data) return; // ya cargada
    startTransition(async () => {
      const res = await getPreparationAction(productionId);
      if (res.status === "ok") setData(res.data);
      else setError(res.message);
    });
  }

  return (
    <>
      <button
        type="button"
        className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium text-brand-700 hover:bg-brand-50"
        onClick={handleOpen}
      >
        <Icon name="recipes" /> Ver preparación
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Lista de preparación"
        >
          <button
            type="button"
            aria-label="Cerrar"
            onClick={() => setOpen(false)}
            className="absolute inset-0 h-full w-full bg-slate-900/50"
          />

          <div className="relative flex max-h-[92vh] w-full max-w-2xl flex-col overflow-y-auto rounded-t-2xl bg-white shadow-xl sm:rounded-2xl">
            <div className="flex items-center justify-between border-b border-brand-100 px-5 py-4">
              <h2 className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                <Icon name="recipes" className="text-brand-500" /> Lista de preparación
              </h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Cerrar"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-brand-100"
              >
                <Icon name="close" />
              </button>
            </div>

            <div className="px-5 py-4">
              {pending && <p className="text-sm text-slate-500">Cargando…</p>}
              {error && (
                <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                  {error}
                </p>
              )}

              {data && (
                <>
                  <div className="mb-4 space-y-0.5 text-sm">
                    <p className="font-semibold text-slate-800">{data.recipe_name}</p>
                    <p className="text-slate-500">
                      {data.product_name ? `Produjo: ${data.product_name} · ` : ""}
                      {formatQuantityUnit(data.quantity_produced, "UNIT", fmt)} producidas
                    </p>
                    <p className="text-xs text-slate-400">
                      {formatDateTime(data.created_at)} · {data.performed_by_email} · costo
                      insumos {formatMoney(data.total_ingredient_cost, fmt)}
                    </p>
                  </div>

                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                        <th className="pb-2">Insumo</th>
                        <th className="pb-2">Ubicación</th>
                        <th className="pb-2 text-right">Cantidad</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.ingredients.map((ing) => (
                        <tr
                          key={ing.supply_item_id}
                          className="border-b border-slate-50 align-top"
                        >
                          <td className="py-2 text-slate-700">{ing.supply_name}</td>
                          <td className="py-2">
                            {ing.location_code ? (
                              <span className="inline-flex items-center gap-1 font-medium text-slate-600">
                                <Icon name="locations" /> {ing.location_code}
                              </span>
                            ) : (
                              <span className="text-slate-400">—</span>
                            )}
                          </td>
                          <td className="py-2 text-right">
                            <span className="font-medium text-slate-700">
                              {formatQuantityUnit(ing.quantity_consumed, ing.unit, fmt)}
                            </span>
                            {ing.batches.length > 0 && (
                              <div className="mt-1 text-[11px] font-normal text-slate-500">
                                {ing.batches.map((b) => (
                                  <div key={b.batch_code}>
                                    {b.batch_code}: {formatQuantityUnit(b.quantity, ing.unit, fmt)}
                                    {b.expiration_date && ` · vence ${formatDate(b.expiration_date)}`}
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>

                  {data.ingredients.length === 0 && (
                    <p className="text-sm text-slate-500">
                      Esta corrida no registró desglose de insumos.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
