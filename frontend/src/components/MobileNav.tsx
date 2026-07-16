"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { logoutAction } from "@/app/actions/auth";
import { Icon } from "@/components/Icon";
import { Sidebar } from "@/components/Sidebar";
import { assetUrl, ROLE_LABELS } from "@/lib/labels";
import type { SessionUser } from "@/lib/session";

interface Props {
  user: SessionUser;
  appName: string;
  /** URL absoluta ya resuelta por assetUrl, o null para el emblema por defecto. */
  logoUrl: string | null;
}

export function MobileNav({ user, appName, logoUrl }: Props) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  useEffect(() => setOpen(false), [pathname]);

  // El drawer ocupa el viewport completo: sin esto el contenido de atrás
  // sigue haciendo scroll bajo el overlay en iOS y Android.
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <>
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-brand-100 bg-white px-4 py-3 md:hidden">
        <Link href="/dashboard" className="flex min-w-0 items-center gap-2">
          {logoUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={logoUrl} alt="" className="h-8 w-8 shrink-0 rounded-lg object-contain" />
          ) : (
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-500 text-white">
              <Icon name="brand" />
            </span>
          )}
          <span className="truncate font-bold text-slate-800">{appName}</span>
        </Link>

        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Abrir menú de navegación"
          aria-expanded={open}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-slate-600 hover:bg-brand-100"
        >
          <Icon name="menu" />
        </button>
      </header>

      {open && (
        <div className="fixed inset-0 z-40 md:hidden">
          <button
            type="button"
            aria-label="Cerrar menú de navegación"
            onClick={() => setOpen(false)}
            className="absolute inset-0 h-full w-full bg-slate-900/40"
          />

          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85%] flex-col overflow-y-auto bg-white p-5 shadow-xl">
            <div className="mb-8 flex items-center justify-between gap-2">
              <div className="flex min-w-0 items-center gap-2">
                {logoUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={logoUrl} alt="" className="h-9 w-9 shrink-0 rounded-xl object-contain" />
                ) : (
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-lg text-white">
                    <Icon name="brand" />
                  </span>
                )}
                <span className="truncate font-bold text-slate-800">{appName}</span>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Cerrar menú de navegación"
                className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-brand-100"
              >
                <Icon name="close" />
              </button>
            </div>

            <Sidebar role={user.role} />

            <div className="mt-auto border-t border-brand-100 pt-4">
              <Link
                href="/profile"
                className="mb-3 flex items-center gap-3 hover:opacity-80"
              >
                <span className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-full border border-brand-100 bg-brand-50 text-brand-300">
                  {assetUrl(user.avatar_url) ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={assetUrl(user.avatar_url)!}
                      alt="Avatar"
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <Icon name="users" />
                  )}
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-sm font-semibold text-slate-700">
                    {user.full_name}
                  </span>
                  <span className="block text-xs text-slate-400">
                    {ROLE_LABELS[user.role]}
                  </span>
                </span>
              </Link>
              <form action={logoutAction}>
                <button type="submit" className="btn-ghost w-full text-xs">
                  <Icon name="logout" /> Cerrar sesión
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
