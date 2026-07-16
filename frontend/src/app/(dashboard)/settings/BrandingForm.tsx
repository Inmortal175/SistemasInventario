"use client";

import { useActionState, useState } from "react";

import { updateBrandingAction } from "@/app/actions/settings";
import { FormMessage } from "@/components/FormMessage";
import { SubmitButton } from "@/components/SubmitButton";
import { IDLE } from "@/lib/form";
import { THEMES } from "@/lib/themes";
import type { ThemeName } from "@/lib/types";

export function BrandingForm({
  appName,
  theme,
  overlayOpacity,
  hasBackground,
}: {
  appName: string;
  theme: ThemeName;
  overlayOpacity: number;
  hasBackground: boolean;
}) {
  const [state, formAction] = useActionState(updateBrandingAction, IDLE);
  const [selected, setSelected] = useState<ThemeName>(theme);
  const [overlay, setOverlay] = useState(overlayOpacity);

  return (
    <form action={formAction} className="space-y-5">
      <div>
        <label htmlFor="app_name" className="label">Nombre del sistema</label>
        <input
          id="app_name"
          name="app_name"
          defaultValue={appName}
          required
          minLength={2}
          maxLength={80}
          className="input"
        />
        <p className="mt-1 text-xs text-slate-400">
          Aparece en el menú, en el login, en el pie de página, en la pestaña del
          navegador y en la documentación de la API.
        </p>
      </div>

      <div>
        <span className="label">Tema de colores</span>
        <input type="hidden" name="theme" value={selected} />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {THEMES.map((t) => {
            const active = t.value === selected;
            return (
              <button
                key={t.value}
                type="button"
                aria-pressed={active}
                onClick={() => setSelected(t.value)}
                className={`rounded-xl border p-3 text-left transition ${
                  active
                    ? "border-brand-500 ring-2 ring-brand-200"
                    : "border-brand-100 hover:border-brand-300"
                }`}
              >
                <span className="mb-2 flex gap-1" aria-hidden>
                  {t.swatch.map((hex) => (
                    <span
                      key={hex}
                      className="h-5 flex-1 rounded"
                      style={{ backgroundColor: hex }}
                    />
                  ))}
                </span>
                <span className="text-xs font-medium text-slate-700">{t.label}</span>
              </button>
            );
          })}
        </div>
        <p className="mt-2 text-xs text-slate-400">
          El cambio aplica a todos los usuarios del sistema.
        </p>
      </div>

      <div>
        <label htmlFor="login_overlay_opacity" className="label">
          Velo sobre el fondo del login: {overlay} %
        </label>
        <input
          id="login_overlay_opacity"
          name="login_overlay_opacity"
          type="range"
          min={0}
          max={80}
          step={5}
          value={overlay}
          onChange={(e) => setOverlay(Number(e.target.value))}
          className="w-full accent-brand-500"
        />
        <div
          className="mt-2 flex h-12 items-center justify-center rounded-lg bg-gradient-to-r from-brand-400 to-brand-700"
          aria-hidden
        >
          <div
            className="flex h-full w-full items-center justify-center rounded-lg bg-slate-900"
            style={{ opacity: overlay / 100 }}
          />
        </div>
        <p className="mt-1 text-xs text-slate-400">
          {hasBackground
            ? "Cuanto más alto, más oscura la foto y más legible el texto."
            : "Sin fondo del login todavía; el velo no se verá hasta que subas uno."}
        </p>
      </div>

      <FormMessage state={state} />

      <SubmitButton className="btn-primary w-full sm:w-auto">
        Guardar cambios
      </SubmitButton>
    </form>
  );
}
