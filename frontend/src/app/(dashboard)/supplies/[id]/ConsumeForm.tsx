"use client";

import { useActionState } from "react";

import { consumeFifoAction } from "@/app/actions/batches";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { MOVEMENT_LABELS, MOVEMENTS_BY_ROLE } from "@/lib/labels";
import type { UserRole } from "@/lib/types";

export function ConsumeForm({
  supplyId,
  role,
}: {
  supplyId: string;
  role: UserRole;
}) {
  const action = consumeFifoAction.bind(null, supplyId);
  const [state, formAction] = useActionState(action, IDLE);

  // FIFO aplica solo a salidas: EXIT y WASTE (intersección con los permitidos por rol).
  const types = MOVEMENTS_BY_ROLE[role].filter(
    (t) => t === "EXIT" || t === "WASTE",
  );

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="movement_type" className="label">Tipo</label>
        <select id="movement_type" name="movement_type" className="input" required>
          {types.map((t) => (
            <option key={t} value={t}>{MOVEMENT_LABELS[t]}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="quantity" className="label">Cantidad</label>
        <input id="quantity" name="quantity" type="number" step="0.001" min="0.001" required className="input" placeholder="0.000" />
      </div>
      <div>
        <label htmlFor="notes" className="label">Notas (opcional)</label>
        <textarea id="notes" name="notes" rows={2} className="input" />
      </div>

      <FormMessage state={state} />
      <SubmitButton pendingText="Descontando…">Consumir (FIFO)</SubmitButton>
    </form>
  );
}
