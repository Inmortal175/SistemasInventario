"use client";

import { useActionState } from "react";

import { registerMovementAction } from "@/app/actions/movements";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { MOVEMENT_LABELS } from "@/lib/labels";
import type { MovementType } from "@/lib/types";

interface SupplyOption {
  id: string;
  label: string;
}

export function MovementForm({
  supplies,
  allowedTypes,
}: {
  supplies: SupplyOption[];
  allowedTypes: MovementType[];
}) {
  const [state, formAction] = useActionState(registerMovementAction, IDLE);

  return (
    <form action={formAction} className="space-y-5">
      <div>
        <label htmlFor="supply_item_id" className="label">Insumo</label>
        <select id="supply_item_id" name="supply_item_id" required className="input">
          <option value="">Selecciona…</option>
          {supplies.map((s) => (
            <option key={s.id} value={s.id}>{s.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="movement_type" className="label">Tipo de movimiento</label>
        <select id="movement_type" name="movement_type" required className="input">
          {allowedTypes.map((t) => (
            <option key={t} value={t}>{MOVEMENT_LABELS[t]}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="quantity" className="label">Cantidad</label>
        <input
          id="quantity"
          name="quantity"
          type="number"
          step="0.001"
          min="0.001"
          required
          placeholder="0.000"
          className="input"
        />
      </div>

      <div>
        <label htmlFor="notes" className="label">Notas (opcional)</label>
        <textarea id="notes" name="notes" rows={2} className="input" />
      </div>

      <FormMessage state={state} />

      <SubmitButton pendingText="Registrando…">Registrar movimiento</SubmitButton>
    </form>
  );
}
