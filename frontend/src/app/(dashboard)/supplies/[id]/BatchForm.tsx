"use client";

import { useActionState } from "react";

import { createBatchAction } from "@/app/actions/batches";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function BatchForm({ supplyId }: { supplyId: string }) {
  const action = createBatchAction.bind(null, supplyId);
  const [state, formAction] = useActionState(action, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="batch_code" className="label">Código de lote</label>
        <input id="batch_code" name="batch_code" required className="input" placeholder="L-CREM-2026-01" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="quantity" className="label">Cantidad</label>
          <input id="quantity" name="quantity" type="number" step="0.001" min="0.001" required className="input" placeholder="10.000" />
        </div>
        <div>
          <label htmlFor="unit_cost" className="label">Costo unit.</label>
          <input id="unit_cost" name="unit_cost" type="number" step="0.0001" min="0" className="input" defaultValue="0" />
        </div>
      </div>
      <div>
        <label htmlFor="expiration_date" className="label">Vencimiento (opcional)</label>
        <input id="expiration_date" name="expiration_date" type="date" className="input" />
      </div>
      <div>
        <label htmlFor="vendor_name" className="label">Proveedor (opcional)</label>
        <input id="vendor_name" name="vendor_name" className="input" placeholder="Proveedor del lote (opcional)" />
      </div>

      <FormMessage state={state} />
      <SubmitButton pendingText="Registrando…">Registrar lote</SubmitButton>
    </form>
  );
}
