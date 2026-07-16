"use client";

import { useActionState } from "react";

import { updateOperationAction } from "@/app/actions/settings";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import type { SystemSettings } from "@/lib/types";

export function OperationForm({ settings }: { settings: SystemSettings }) {
  const [state, formAction] = useActionState(updateOperationAction, IDLE);

  return (
    <form action={formAction} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="expiration_alert_days" className="label">
            Avisar vencimiento con (días)
          </label>
          <input
            id="expiration_alert_days"
            name="expiration_alert_days"
            type="number"
            min={1}
            max={90}
            defaultValue={settings.expiration_alert_days}
            required
            className="input"
          />
          <p className="mt-1 text-xs text-slate-400">
            Cuántos días antes de vencer se alerta de un lote.
          </p>
        </div>

        <div>
          <label htmlFor="page_size" className="label">Registros por página</label>
          <input
            id="page_size"
            name="page_size"
            type="number"
            min={5}
            max={100}
            defaultValue={settings.page_size}
            required
            className="input"
          />
          <p className="mt-1 text-xs text-slate-400">
            Aplica al catálogo de insumos y a la auditoría.
          </p>
        </div>

        <div>
          <label htmlFor="currency_code" className="label">Moneda (ISO 4217)</label>
          <input
            id="currency_code"
            name="currency_code"
            defaultValue={settings.currency_code}
            pattern="[A-Za-z]{3}"
            maxLength={3}
            required
            className="input uppercase"
          />
          <p className="mt-1 text-xs text-slate-400">PEN, USD, EUR…</p>
        </div>

        <div>
          <label htmlFor="locale" className="label">Formato regional</label>
          <input
            id="locale"
            name="locale"
            defaultValue={settings.locale}
            pattern="[a-z]{2}(-[A-Z]{2})?"
            maxLength={5}
            required
            className="input"
          />
          <p className="mt-1 text-xs text-slate-400">
            es-PE, es-MX, en-US… decide separadores de miles y decimales.
          </p>
        </div>
      </div>

      <FormMessage state={state} />

      <SubmitButton className="btn-primary w-full sm:w-auto">
        Guardar operación
      </SubmitButton>
    </form>
  );
}
