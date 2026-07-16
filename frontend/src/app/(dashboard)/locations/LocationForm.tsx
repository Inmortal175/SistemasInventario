"use client";

import { useActionState, useEffect, useRef } from "react";

import { createLocationAction } from "@/app/actions/locations";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { LOCATION_TYPE_LABELS } from "@/lib/labels";
import type { LocationType } from "@/lib/types";

const TYPES = Object.keys(LOCATION_TYPE_LABELS) as LocationType[];

export function LocationForm() {
  const [state, formAction] = useActionState(createLocationAction, IDLE);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (state.status === "success") formRef.current?.reset();
  }, [state]);

  return (
    <form ref={formRef} action={formAction} className="space-y-4">
      <div>
        <label htmlFor="code" className="label">Código</label>
        <input
          id="code"
          name="code"
          required
          placeholder="EST-01-F2"
          className="input uppercase"
        />
        <p className="mt-1 text-xs text-slate-400">
          Prefijos: EST, REF, FRZ, CAB, CON, ALM. Solo EST admite fila (-F).
        </p>
      </div>
      <div>
        <label htmlFor="location_type" className="label">Tipo</label>
        <select id="location_type" name="location_type" required className="input">
          {TYPES.map((t) => (
            <option key={t} value={t}>{LOCATION_TYPE_LABELS[t]}</option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="capacity_units" className="label">Capacidad (opcional)</label>
        <input
          id="capacity_units"
          name="capacity_units"
          type="number"
          min="1"
          placeholder="p. ej. 100"
          className="input"
        />
      </div>
      <div>
        <label htmlFor="description" className="label">Descripción (opcional)</label>
        <input id="description" name="description" className="input" placeholder="Estante 01, fila 2 — harinas (opcional)" />
      </div>

      <FormMessage state={state} />

      <SubmitButton className="btn-primary w-full">Crear ubicación</SubmitButton>
    </form>
  );
}
