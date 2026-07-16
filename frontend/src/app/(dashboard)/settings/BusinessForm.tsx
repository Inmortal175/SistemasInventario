"use client";

import { useActionState } from "react";

import { updateBusinessAction } from "@/app/actions/settings";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import type { SystemSettings } from "@/lib/types";

export function BusinessForm({ settings }: { settings: SystemSettings }) {
  const [state, formAction] = useActionState(updateBusinessAction, IDLE);

  return (
    <form action={formAction} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="business_name" className="label">Razón social</label>
          <input
            id="business_name"
            name="business_name"
            defaultValue={settings.business_name ?? ""}
            maxLength={150}
            placeholder="Mi Pastelería S.A.C."
            className="input"
          />
        </div>
        <div>
          <label htmlFor="tax_id" className="label">RUC</label>
          <input
            id="tax_id"
            name="tax_id"
            defaultValue={settings.tax_id ?? ""}
            maxLength={20}
            inputMode="numeric"
            placeholder="20123456789"
            className="input"
          />
        </div>
        <div className="sm:col-span-2">
          <label htmlFor="address" className="label">Dirección</label>
          <input
            id="address"
            name="address"
            defaultValue={settings.address ?? ""}
            maxLength={255}
            placeholder="Av. Mariscal Cáceres 123, Ayacucho"
            className="input"
          />
        </div>
        <div>
          <label htmlFor="phone" className="label">Teléfono</label>
          <input
            id="phone"
            name="phone"
            defaultValue={settings.phone ?? ""}
            maxLength={30}
            placeholder="+51 966 123 456"
            className="input"
          />
        </div>
      </div>

      <p className="text-xs text-slate-400">
        Todavía no se imprimen en ningún lado: quedan guardados para el día que los
        reportes lleven membrete. Deja un campo vacío para borrarlo.
      </p>

      <FormMessage state={state} />

      <SubmitButton className="btn-primary w-full sm:w-auto">
        Guardar datos
      </SubmitButton>
    </form>
  );
}
