"use client";

import { useActionState } from "react";

import { loginAction } from "@/app/actions/auth";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

export function LoginForm() {
  const [state, formAction] = useActionState(loginAction, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="email" className="label">
          Correo electrónico
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="username"
          required
          className="input"
          placeholder="admin@pasteleria.com"
        />
      </div>

      <div>
        <label htmlFor="password" className="label">
          Contraseña
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          className="input"
          placeholder="••••••••"
        />
      </div>

      <FormMessage state={state} />

      <SubmitButton className="btn-primary w-full" pendingText="Ingresando…">
        Iniciar sesión
      </SubmitButton>
    </form>
  );
}
