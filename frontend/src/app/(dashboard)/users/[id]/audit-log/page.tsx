import Link from "next/link";
import { redirect } from "next/navigation";

import { Icon } from "@/components/Icon";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { actionLabel, formatDateTime } from "@/lib/labels";
import { getSettings, getUserAuditLog } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

export default async function AuditLogPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ page?: string }>;
}) {
  const me = await getSessionUser();
  if (!me || me.role !== "SUPERADMIN") redirect("/dashboard");

  const [{ id }, { page: rawPage }, settings] = await Promise.all([
    params,
    searchParams,
    getSettings(),
  ]);
  const page = Math.max(1, Number(rawPage) || 1);
  const log = await getUserAuditLog(id, page, settings.page_size);

  // Página fuera de rango: mejor volver al inicio que fingir que no hay nada.
  if (page > 1 && log.entries.length === 0 && log.total > 0) {
    redirect(`/users/${id}/audit-log`);
  }

  return (
    <>
      <PageHeader
        title="Auditoría de usuario"
        subtitle={`${log.email} · ${log.total} acción(es)`}
        action={
          <Link href="/users" className="btn-ghost">
            ← Volver
          </Link>
        }
      />

      {log.entries.length === 0 ? (
        <div className="card text-sm text-slate-500">
          Este usuario no tiene acciones registradas.
        </div>
      ) : (
        <div className="card divide-y divide-brand-50 p-0">
          {log.entries.map((e) => (
            <div key={e.entity_id + e.action_type} className="flex items-start gap-3 px-6 py-4">
              <span className="mt-0.5 text-brand-400">
                <Icon name="movements" />
              </span>
              <div className="flex-1">
                <p className="text-sm text-slate-800">{e.summary}</p>
                <p className="text-xs text-slate-400">
                  <span className="font-medium text-slate-500">{actionLabel(e.action_type)}</span>{" "}
                  · {formatDateTime(e.timestamp)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      <Pagination
        page={log.page}
        limit={log.limit}
        total={log.total}
        basePath={`/users/${id}/audit-log`}
        noun="acciones"
      />
    </>
  );
}
