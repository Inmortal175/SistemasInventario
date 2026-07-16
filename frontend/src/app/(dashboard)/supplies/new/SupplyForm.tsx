"use client";

import Link from "next/link";
import { useActionState } from "react";

import { createSupplyAction } from "@/app/actions/supplies";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { UNIT_LABELS } from "@/lib/labels";
import type { Category, Location, UnitMeasure } from "@/lib/types";

const UNITS = Object.keys(UNIT_LABELS) as UnitMeasure[];

export function SupplyForm({
  categories,
  locations,
}: {
  categories: Category[];
  locations: Location[];
}) {
  const [state, formAction] = useActionState(createSupplyAction, IDLE);

  return (
    <form action={formAction} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="name" className="label">Nombre</label>
          <input id="name" name="name" required className="input" placeholder="Harina de trigo sin preparar" />
        </div>
        <div>
          <label htmlFor="sku" className="label">SKU</label>
          <input id="sku" name="sku" required className="input" placeholder="HAR-001" />
        </div>
      </div>

      <div>
        <label htmlFor="description" className="label">Descripción (opcional)</label>
        <input id="description" name="description" className="input" placeholder="Descripción del insumo (opcional)" />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="category_id" className="label">Categoría</label>
          <select id="category_id" name="category_id" required className="input">
            <option value="">Selecciona…</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="location_id" className="label">Ubicación</label>
          <select id="location_id" name="location_id" required className="input">
            <option value="">Selecciona…</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>{l.code}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="unit_of_measure" className="label">Unidad de medida</label>
          <select id="unit_of_measure" name="unit_of_measure" required className="input">
            {UNITS.map((u) => (
              <option key={u} value={u}>{UNIT_LABELS[u]}</option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="unit_cost" className="label">Costo unitario</label>
          <input
            id="unit_cost"
            name="unit_cost"
            type="number"
            step="0.0001"
            min="0"
            defaultValue="0"
            className="input"
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label htmlFor="current_stock" className="label">Stock actual</label>
          <input
            id="current_stock"
            name="current_stock"
            type="number"
            step="0.001"
            min="0"
            defaultValue="0"
            className="input"
          />
        </div>
        <div>
          <label htmlFor="minimum_stock" className="label">Stock mínimo</label>
          <input
            id="minimum_stock"
            name="minimum_stock"
            type="number"
            step="0.001"
            min="0"
            defaultValue="0"
            className="input"
          />
        </div>
        <div>
          <label htmlFor="maximum_stock" className="label">Stock máximo</label>
          <input
            id="maximum_stock"
            name="maximum_stock"
            type="number"
            step="0.001"
            min="0"
            defaultValue="0"
            className="input"
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="supplier_name" className="label">Proveedor (opcional)</label>
          <input id="supplier_name" name="supplier_name" className="input" placeholder="Molinos Anita (opcional)" />
        </div>
        <div>
          <label htmlFor="expiration_date" className="label">Vencimiento (opcional)</label>
          <input id="expiration_date" name="expiration_date" type="date" className="input" />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input type="checkbox" name="is_perishable" className="h-4 w-4 rounded" />
        Es perecedero
      </label>

      <FormMessage state={state} />

      <div className="flex gap-3">
        <SubmitButton>Registrar insumo</SubmitButton>
        <Link href="/supplies" className="btn-ghost">Cancelar</Link>
      </div>
    </form>
  );
}
