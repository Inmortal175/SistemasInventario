"use client";

import { useActionState } from "react";

import { createUserAction } from "@/app/actions/users";
import { FormMessage } from "@/components/FormMessage";
import { PasswordInput } from "@/components/PasswordInput";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { ROLE_LABELS } from "@/lib/labels";
import type { UserRole } from "@/lib/types";

const ROLES: UserRole[] = ["STAFF", "ADMIN", "SUPERADMIN"];

export function UserForm() {
  const [state, formAction] = useActionState(createUserAction, IDLE);

  return (
    <form action={formAction} className="space-y-4">
      <div>
        <label htmlFor="full_name" className="label">Nombre completo</label>
        <input id="full_name" name="full_name" required className="input" placeholder="María Pérez" />
      </div>
      <div>
        <label htmlFor="email" className="label">Email</label>
        <input id="email" name="email" type="email" required className="input" placeholder="maria@pasteleria.com" />
      </div>
      <div>
        <label htmlFor="password" className="label">Contraseña</label>
        <PasswordInput id="password" name="password" autoComplete="new-password" required minLength={8} placeholder="Mínimo 8 caracteres" />
      </div>
      <div>
        <label htmlFor="role" className="label">Rol</label>
        <select id="role" name="role" className="input" defaultValue="STAFF">
          {ROLES.map((r) => (
            <option key={r} value={r}>{ROLE_LABELS[r]}</option>
          ))}
        </select>
      </div>

      <FormMessage state={state} />
      <SubmitButton pendingText="Creando…">Crear usuario</SubmitButton>
    </form>
  );
}
