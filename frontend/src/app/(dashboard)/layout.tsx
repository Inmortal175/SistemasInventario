import Link from "next/link";
import { redirect } from "next/navigation";

import { logoutAction } from "@/app/actions/auth";
import { AlertToaster } from "@/components/AlertToaster";
import { Footer } from "@/components/Footer";
import { Icon } from "@/components/Icon";
import { MobileNav } from "@/components/MobileNav";
import { Sidebar } from "@/components/Sidebar";
import { assetUrl, isAdmin, ROLE_LABELS } from "@/lib/labels";
import { getSettings } from "@/lib/queries";
import { getSessionUser, getToken } from "@/lib/session";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getSessionUser();
  if (!user) redirect("/login");

  const [settings, token] = await Promise.all([
    getSettings(),
    isAdmin(user.role) ? getToken() : Promise.resolve(null),
  ]);
  const logo = assetUrl(settings.logo_url);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      {/* `h-screen` + `sticky` fijan el menú al viewport: sin ellos el <aside>
          se estira con la tabla y el bloque de perfil se hunde fuera de vista. */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-brand-100 bg-white p-5 md:flex">
        <div className="mb-8 flex shrink-0 items-center gap-2">
          {logo ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={logo}
              alt=""
              className="h-9 w-9 shrink-0 rounded-xl object-contain"
            />
          ) : (
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-500 text-lg text-white">
              <Icon name="brand" />
            </span>
          )}
          <span className="truncate font-bold text-slate-800">
            {settings.app_name}
          </span>
        </div>

        {/* Si algún día hay más entradas que alto de pantalla, scrollea el nav,
            no la página entera. */}
        <div className="-mr-2 min-h-0 flex-1 overflow-y-auto pr-2">
          <Sidebar role={user.role} />
        </div>

        <div className="mt-auto shrink-0 border-t border-brand-100 pt-4">
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
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <MobileNav user={user} appName={settings.app_name} logoUrl={logo} />

        <main className="flex-1 overflow-x-hidden px-4 py-6 sm:px-5 sm:py-8 md:px-10">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>

        <Footer appName={settings.app_name} />
      </div>

      {/* HU-14: alertas en tiempo real vía WebSocket, solo para ADMIN+ */}
      {isAdmin(user.role) && <AlertToaster token={token} />}
    </div>
  );
}
