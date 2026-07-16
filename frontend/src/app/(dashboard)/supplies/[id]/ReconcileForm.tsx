"use client";

import { useActionState } from "react";

import { reconcileAction } from "@/app/actions/batches";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function ReconcileForm({ supplyId }: { supplyId: string }) {
  const action = reconcileAction.bind(null, supplyId);
  const [state, formAction] = useActionState(action, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="physical_stock" className="label">Stock físico contado</label>
        <input id="physical_stock" name="physical_stock" type="number" step="0.001" min="0" required className="input" placeholder="Conteo físico real" />
      </div>
      <div>
        <label htmlFor="reason" className="label">Motivo del ajuste</label>
        <textarea id="reason" name="reason" rows={2} required className="input" placeholder="Error de digitación en el registro anterior" />
      </div>

      <FormMessage state={state} />
      <SubmitButton pendingText="Aplicando…">Conciliar</SubmitButton>
    </form>
  );
}
