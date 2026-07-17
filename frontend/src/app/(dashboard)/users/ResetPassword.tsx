"use client";

import { useActionState, useState } from "react";

import { resetPasswordAction } from "@/app/actions/users";
import { FormMessage } from "@/components/FormMessage";
import { PasswordInput } from "@/components/PasswordInput";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function ResetPassword({ userId }: { userId: string }) {
  const [open, setOpen] = useState(false);
  const action = resetPasswordAction.bind(null, userId);
  const [state, formAction] = useActionState(action, IDLE);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="rounded-lg bg-brand-100 px-2 py-1 text-xs font-medium text-brand-700 hover:bg-brand-200"
      >
        Contraseña
      </button>
    );
  }

  return (
    <form action={formAction} className="flex flex-col gap-2">
      <PasswordInput
        name="new_password"
        autoComplete="new-password"
        required
        minLength={8}
        placeholder="Nueva contraseña"
        className="input py-1 text-xs"
      />
      <div className="flex gap-2">
        <SubmitButton
          pendingText="…"
          className="btn-primary px-2 py-1 text-xs"
        >
          Guardar
        </SubmitButton>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:text-slate-600"
        >
          Cancelar
        </button>
      </div>
      <FormMessage state={state} />
    </form>
  );
}
