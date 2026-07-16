"use client";

import { useActionState } from "react";

import { updateProfileAction } from "@/app/actions/profile";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function ProfileForm({ currentName }: { currentName: string }) {
  const [state, formAction] = useActionState(updateProfileAction, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="full_name" className="label">Nombre completo</label>
        <input
          id="full_name"
          name="full_name"
          required
          minLength={2}
          defaultValue={currentName}
          className="input"
        />
      </div>
      <FormMessage state={state} />
      <SubmitButton pendingText="Guardando…">Guardar cambios</SubmitButton>
    </form>
  );
}
