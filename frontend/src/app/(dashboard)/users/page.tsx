import Link from "next/link";
import { redirect } from "next/navigation";

import {
  reactivateUserAction,
  suspendUserAction,
} from "@/app/actions/users";
import { Icon } from "@/components/Icon";
import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { formatDate, ROLE_LABELS } from "@/lib/labels";
import { getUsers } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { ResetPassword } from "./ResetPassword";
import { UserForm } from "./UserForm";

export default async function UsersPage() {
  const me = await getSessionUser();
  if (!me || me.role !== "SUPERADMIN") redirect("/dashboard");

  const users = await getUsers();

  return (
    <>
      <PageHeader
        title="Usuarios"
        subtitle="Gestión de cuentas y trazabilidad (solo Superadmin)"
      />

      <InfoBanner>
        Crea cuentas y asigna roles. <strong>Contraseña</strong> restablece la clave de un
        usuario que la olvidó (sus sesiones activas se cierran). <strong>Suspender</strong>
        bloquea el acceso al instante y <strong>Reactivar</strong> lo devuelve;{" "}
        <strong>Auditoría</strong> lista todo lo que ese usuario ha registrado.
      </InfoBanner>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <section className="lg:col-span-2">
          <div className="card overflow-x-auto p-0">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-brand-100 text-left text-xs uppercase text-slate-400">
                  <th className="px-6 py-3 font-medium">Usuario</th>
                  <th className="px-6 py-3 font-medium">Rol</th>
                  <th className="px-6 py-3 font-medium">Estado</th>
                  <th className="px-6 py-3 text-right font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-50">
                {users.items.map((u) => {
                  const isSelf = u.id === me.id;
                  return (
                    <tr key={u.id} className="hover:bg-brand-50/40">
                      <td className="px-6 py-3">
                        <p className="font-medium text-slate-800">{u.full_name}</p>
                        <p className="text-xs text-slate-400">{u.email}</p>
                        <p className="text-[11px] text-slate-300">
                          Desde {formatDate(u.created_at)}
                        </p>
                      </td>
                      <td className="px-6 py-3 text-slate-600">
                        {ROLE_LABELS[u.role]}
                      </td>
                      <td className="px-6 py-3">
                        {u.is_active ? (
                          <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                            activo
                          </span>
                        ) : (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-600">
                            suspendido
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-3">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/users/${u.id}/audit-log`}
                            className="text-xs font-medium text-brand-600 hover:underline"
                          >
                            Auditoría
                          </Link>
                          {!isSelf && <ResetPassword userId={u.id} />}
                          {!isSelf &&
                            (u.is_active ? (
                              <form action={suspendUserAction.bind(null, u.id)}>
                                <button
                                  type="submit"
                                  className="rounded-lg bg-red-50 px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-100"
                                >
                                  Suspender
                                </button>
                              </form>
                            ) : (
                              <form action={reactivateUserAction.bind(null, u.id)}>
                                <button
                                  type="submit"
                                  className="rounded-lg bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100"
                                >
                                  Reactivar
                                </button>
                              </form>
                            ))}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-800">
            <Icon name="add" className="text-brand-500" /> Nuevo usuario
          </h2>
          <div className="card">
            <UserForm />
          </div>
        </section>
      </div>
    </>
  );
}
