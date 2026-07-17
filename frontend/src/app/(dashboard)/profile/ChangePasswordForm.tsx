"use client";

import { useActionState } from "react";

import { changePasswordAction } from "@/app/actions/profile";
import { FormMessage } from "@/components/FormMessage";
import { PasswordInput } from "@/components/PasswordInput";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function ChangePasswordForm() {
  const [state, formAction] = useActionState(changePasswordAction, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="current_password" className="label">Contraseña actual</label>
        <PasswordInput
          id="current_password"
          name="current_password"
          autoComplete="current-password"
          required
          placeholder="Contraseña actual"
        />
      </div>
      <div>
        <label htmlFor="new_password" className="label">Nueva contraseña</label>
        <PasswordInput
          id="new_password"
          name="new_password"
          autoComplete="new-password"
          required
          minLength={8}
          placeholder="Mínimo 8 caracteres"
        />
      </div>
      <div>
        <label htmlFor="confirm_password" className="label">Confirmar nueva</label>
        <PasswordInput
          id="confirm_password"
          name="confirm_password"
          autoComplete="new-password"
          required
          minLength={8}
          placeholder="Repite la nueva contraseña"
        />
      </div>
      <FormMessage state={state} />
      <SubmitButton pendingText="Cambiando…">Cambiar contraseña</SubmitButton>
    </form>
  );
}
