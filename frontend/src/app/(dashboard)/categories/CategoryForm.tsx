"use client";

import { useActionState, useEffect, useRef, useState } from "react";

import { createCategoryAction } from "@/app/actions/categories";
import { FormMessage } from "@/components/FormMessage";
import { IconPicker } from "@/components/IconPicker";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";

const DEFAULT_COLOR = "#FF6B9D";

export function CategoryForm() {
  const [state, formAction] = useActionState(createCategoryAction, IDLE);
  const formRef = useRef<HTMLFormElement>(null);
  const [color, setColor] = useState(DEFAULT_COLOR);
  const [icon, setIcon] = useState<string | null>(null);

  useEffect(() => {
    if (state.status === "success") {
      formRef.current?.reset();
      setColor(DEFAULT_COLOR);
      setIcon(null);
    }
  }, [state]);

  return (
    <form ref={formRef} action={formAction} className="space-y-4">
      <div>
        <label htmlFor="name" className="label">Nombre</label>
        <input id="name" name="name" required className="input" placeholder="Chocolatería" />
      </div>
      <div>
        <label htmlFor="color_hex" className="label">Color</label>
        <input
          id="color_hex"
          name="color_hex"
          type="color"
          value={color}
          onChange={(e) => setColor(e.target.value)}
          className="h-10 w-full cursor-pointer rounded-lg border border-slate-300"
        />
      </div>
      <div>
        <span className="label">Ícono (opcional)</span>
        <input type="hidden" name="icon_name" value={icon ?? ""} />
        <IconPicker value={icon} onChange={setIcon} color={color} />
      </div>
      <div>
        <label htmlFor="description" className="label">Descripción (opcional)</label>
        <input id="description" name="description" className="input" placeholder="Cacao, coberturas y derivados (opcional)" />
      </div>

      <FormMessage state={state} />

      <SubmitButton className="btn-primary w-full">Crear categoría</SubmitButton>
    </form>
  );
}
