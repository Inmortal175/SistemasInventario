"use client";

import { useState, type ComponentPropsWithoutRef } from "react";

import { Icon } from "@/components/Icon";

type PasswordInputProps = Omit<ComponentPropsWithoutRef<"input">, "type">;

/** Campo de contraseña con botón para revelar u ocultar el valor.
 *
 *  Acepta las props nativas de <input>, así que sustituye a un
 *  `<input type="password">` sin más cambios en el formulario. */
export function PasswordInput({ className = "input", ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);

  return (
    <div className="relative">
      <input
        {...props}
        type={visible ? "text" : "password"}
        className={`${className} pr-10`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        aria-pressed={visible}
        title={visible ? "Ocultar contraseña" : "Mostrar contraseña"}
        className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 transition hover:text-slate-600"
      >
        <Icon name={visible ? "eyeSlash" : "eye"} fixedWidth />
      </button>
    </div>
  );
}
