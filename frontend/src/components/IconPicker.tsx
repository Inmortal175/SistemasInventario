"use client";

import { useEffect, useState } from "react";

import { CategoryIcon } from "@/components/CategoryIcon";
import { Icon } from "@/components/Icon";
import { CATEGORY_ICON_GROUPS } from "@/lib/categoryIcons";

interface Props {
  value: string | null;
  onChange: (icon: string | null) => void;
  /** Color de fondo de la vista previa; sigue al selector de color del form. */
  color?: string;
}

export function IconPicker({ value: selected, onChange, color }: Props) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <div className="flex items-center gap-3">
        <span
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg text-white"
          style={{ backgroundColor: color || "#f83b7e" }}
          aria-hidden
        >
          {selected ? (
            <CategoryIcon name={selected} />
          ) : (
            <span className="text-xs font-semibold opacity-70">—</span>
          )}
        </span>

        <button
          type="button"
          onClick={() => setOpen(true)}
          className="btn-ghost text-xs"
        >
          {selected ? "Cambiar ícono" : "Elegir ícono"}
        </button>

        {selected && (
          <button
            type="button"
            onClick={() => onChange(null)}
            className="text-xs text-slate-400 underline hover:text-slate-600"
          >
            Quitar
          </button>
        )}
      </div>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4"
          role="dialog"
          aria-modal="true"
          aria-label="Selector de ícono"
        >
          <button
            type="button"
            aria-label="Cerrar selector"
            onClick={() => setOpen(false)}
            className="absolute inset-0 h-full w-full bg-slate-900/40"
          />

          <div className="relative flex max-h-[85vh] w-full max-w-lg flex-col overflow-hidden rounded-t-2xl bg-white shadow-xl sm:rounded-2xl">
            <div className="flex items-center justify-between border-b border-brand-100 px-5 py-4">
              <h2 className="text-sm font-semibold text-slate-800">
                Elige un ícono
              </h2>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Cerrar selector"
                className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-brand-100"
              >
                <Icon name="close" />
              </button>
            </div>

            <div className="overflow-y-auto px-5 py-4">
              {CATEGORY_ICON_GROUPS.map((group) => (
                <section key={group.label} className="mb-5 last:mb-0">
                  <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                    {group.label}
                  </h3>
                  <div className="grid grid-cols-5 gap-2 sm:grid-cols-6">
                    {group.icons.map((iconName) => {
                      const active = iconName === selected;
                      return (
                        <button
                          key={iconName}
                          type="button"
                          title={iconName}
                          aria-pressed={active}
                          onClick={() => {
                            onChange(iconName);
                            setOpen(false);
                          }}
                          className={`flex aspect-square items-center justify-center rounded-xl border text-lg transition ${
                            active
                              ? "border-brand-500 bg-brand-500 text-white"
                              : "border-brand-100 text-slate-500 hover:border-brand-300 hover:bg-brand-50"
                          }`}
                        >
                          <CategoryIcon name={iconName} />
                        </button>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
