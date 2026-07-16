"use client";

import { useActionState } from "react";

import { changePasswordAction } from "@/app/actions/profile";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function ChangePasswordForm() {
  const [state, formAction] = useActionState(changePasswordAction, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="current_password" className="label">Contraseña actual</label>
        <input
          id="current_password"
          name="current_password"
          type="password"
          required
          placeholder="Contraseña actual"
          className="input"
        />
      </div>
      <div>
        <label htmlFor="new_password" className="label">Nueva contraseña</label>
        <input
          id="new_password"
          name="new_password"
          type="password"
          required
          minLength={8}
          placeholder="Mínimo 8 caracteres"
          className="input"
        />
      </div>
      <div>
        <label htmlFor="confirm_password" className="label">Confirmar nueva</label>
        <input
          id="confirm_password"
          name="confirm_password"
          type="password"
          required
          minLength={8}
          placeholder="Repite la nueva contraseña"
          className="input"
        />
      </div>
      <FormMessage state={state} />
      <SubmitButton pendingText="Cambiando…">Cambiar contraseña</SubmitButton>
    </form>
  );
}
