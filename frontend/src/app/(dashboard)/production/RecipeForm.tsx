"use client";

import { useActionState, useState } from "react";

import { createRecipeAction } from "@/app/actions/production";
import { FormMessage } from "@/components/FormMessage";
import { Icon } from "@/components/Icon";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { UNIT_LABELS } from "@/lib/labels";
import type { UnitMeasure } from "@/lib/types";

interface SupplyOption {
  id: string;
  label: string;
}

const UNITS = Object.keys(UNIT_LABELS) as UnitMeasure[];

interface LocationOption {
  id: string;
  label: string;
}

export function RecipeForm({
  supplies,
  locations,
}: {
  supplies: SupplyOption[];
  locations: LocationOption[];
}) {
  const [state, formAction] = useActionState(createRecipeAction, IDLE);
  // Filas de ingredientes: solo un contador de claves para renderizar/borrar.
  const [rows, setRows] = useState<number[]>([0]);
  const [nextId, setNextId] = useState(1);
  // Si la receta produce un producto terminado, se revela su definición.
  const [makesProduct, setMakesProduct] = useState(false);

  function addRow() {
    setRows((r) => [...r, nextId]);
    setNextId((n) => n + 1);
  }

  function removeRow(id: number) {
    setRows((r) => (r.length > 1 ? r.filter((x) => x !== id) : r));
  }

  return (
    <form action={formAction} className="space-y-5">
      <div>
        <label htmlFor="name" className="label">Nombre de la receta</label>
        <input id="name" name="name" required className="input" placeholder="Torta de Chocolate" />
      </div>

      <div>
        <label htmlFor="description" className="label">Descripción (opcional)</label>
        <input id="description" name="description" className="input" placeholder="Torta húmeda, molde 22 cm (opcional)" />
      </div>

      <div>
        <label htmlFor="yield_unit" className="label">Unidad de rendimiento</label>
        <select id="yield_unit" name="yield_unit" className="input" defaultValue="UNIT">
          {UNITS.map((u) => (
            <option key={u} value={u}>{UNIT_LABELS[u]}</option>
          ))}
        </select>
      </div>

      <div className="rounded-lg border border-brand-100 bg-brand-50/40 p-3">
        <label className="flex items-start gap-2 text-sm text-slate-700">
          <input
            type="checkbox"
            name="makes_product"
            className="mt-0.5 h-4 w-4 rounded"
            checked={makesProduct}
            onChange={(e) => setMakesProduct(e.target.checked)}
          />
          <span>
            Esta receta produce un <strong>producto terminado</strong> (p. ej. una torta que se
            guarda en refri para vender). Se crea solo — no hace falta registrarlo como insumo.
          </span>
        </label>

        {makesProduct && (
          <div className="mt-3 space-y-3">
            <div>
              <label htmlFor="product_name" className="label">Nombre del producto</label>
              <input
                id="product_name"
                name="product_name"
                className="input"
                placeholder="Torta de Chocolate"
                required={makesProduct}
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label htmlFor="product_location_id" className="label">Ubicación (refri)</label>
                <select
                  id="product_location_id"
                  name="product_location_id"
                  className="input"
                  defaultValue=""
                  required={makesProduct}
                >
                  <option value="">Selecciona…</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>{l.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="shelf_life_days" className="label">Vida útil (días)</label>
                <input
                  id="shelf_life_days"
                  name="shelf_life_days"
                  type="number"
                  min="0"
                  step="1"
                  className="input"
                  placeholder="p. ej. 4"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div>
        <p className="label">Ingredientes (por unidad producida)</p>
        <div className="space-y-2">
          {rows.map((id) => (
            <div key={id} className="flex items-center gap-2">
              <select name="supply_item_id" className="input flex-1" required>
                <option value="">Insumo…</option>
                {supplies.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
              <input
                name="quantity_per_unit"
                type="number"
                step="0.001"
                min="0.001"
                required
                className="input w-28"
                placeholder="Cant."
              />
              <button
                type="button"
                onClick={() => removeRow(id)}
                className="rounded-lg px-2 py-2 text-slate-400 hover:text-red-500"
                aria-label="Quitar ingrediente"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
        <button
          type="button"
          onClick={addRow}
          className="mt-2 text-sm font-medium text-brand-600"
        >
          <Icon name="add" /> Agregar ingrediente
        </button>
      </div>

      <FormMessage state={state} />

      <SubmitButton pendingText="Creando…">Crear receta</SubmitButton>
    </form>
  );
}
