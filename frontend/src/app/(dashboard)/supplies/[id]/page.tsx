import Link from "next/link";
import { notFound } from "next/navigation";

import { Icon } from "@/components/Icon";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { formatConfig } from "@/lib/format";
import {
  formatDate,
  formatDateTime,
  formatMoney,
  formatQuantity,
  isAdmin,
  MOVEMENT_LABELS,
  UNIT_LABELS,
} from "@/lib/labels";
import {
  getSettings,
  getSupply,
  getSupplyBatches,
  getSupplyMovements,
} from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

const MOVEMENTS_PAGE_SIZE = 10;

import { BatchForm } from "./BatchForm";
import { ConsumeForm } from "./ConsumeForm";
import { ReconcileForm } from "./ReconcileForm";

export default async function SupplyDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ mpage?: string }>;
}) {
  const [{ id }, { mpage }] = await Promise.all([params, searchParams]);
  const movementsPage = Math.max(1, Number(mpage) || 1);

  let supply;
  try {
    supply = await getSupply(id);
  } catch {
    notFound();
  }

  const [batches, movements, user, settings] = await Promise.all([
    getSupplyBatches(id).catch(() => ({ items: [], total: 0, total_stock: "0" })),
    getSupplyMovements(id, movementsPage, MOVEMENTS_PAGE_SIZE).catch(() => ({
      items: [],
      total: 0,
      page: 1,
      limit: MOVEMENTS_PAGE_SIZE,
    })),
    getSessionUser(),
    getSettings(),
  ]);

  const fmt = formatConfig(settings);
  const admin = user ? isAdmin(user.role) : false;
  const unit = UNIT_LABELS[supply.unit_of_measure];

  return (
    <>
      <PageHeader
        title={supply.name}
        subtitle={`SKU ${supply.sku} · ${unit}`}
        action={
          <Link href="/supplies" className="btn-ghost">
            ← Volver
          </Link>
        }
      />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="card">
          <p className="text-sm text-slate-500">Stock actual</p>
          <p
            className={`mt-1 text-2xl font-bold ${
              supply.is_below_minimum ? "text-red-600" : "text-slate-800"
            }`}
          >
            {formatQuantity(supply.current_stock, fmt)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Mínimo</p>
          <p className="mt-1 text-2xl font-bold text-slate-800">
            {formatQuantity(supply.minimum_stock, fmt)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Costo unitario</p>
          <p className="mt-1 text-2xl font-bold text-slate-800">
            {formatMoney(supply.unit_cost, fmt)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-slate-500">Lotes activos</p>
          <p className="mt-1 text-2xl font-bold text-slate-800">{batches.total}</p>
        </div>
      </div>

      {/* Lotes */}
      <section className="mt-8">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-800">
          <Icon name="batches" className="text-brand-500" /> Lotes (orden FIFO)
        </h2>
        {batches.items.length === 0 ? (
          <div className="card text-sm text-slate-500">
            Este insumo no tiene lotes registrados.
          </div>
        ) : (
          <div className="card overflow-x-auto p-0">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-brand-100 text-left text-xs uppercase text-slate-400">
                  <th className="px-6 py-3 font-medium">Lote</th>
                  <th className="px-6 py-3 font-medium">Vence</th>
                  <th className="px-6 py-3 text-right font-medium">Stock</th>
                  <th className="px-6 py-3 text-right font-medium">Costo unit.</th>
                  <th className="px-6 py-3 font-medium">Proveedor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-50">
                {batches.items.map((b) => (
                  <tr key={b.id} className="hover:bg-brand-50/40">
                    <td className="px-6 py-3 font-medium text-slate-800">
                      {b.batch_code}
                    </td>
                    <td className="px-6 py-3 text-slate-600">
                      {formatDate(b.expiration_date)}
                    </td>
                    <td className="px-6 py-3 text-right text-slate-800">
                      {formatQuantity(b.current_stock, fmt)}
                    </td>
                    <td className="px-6 py-3 text-right text-slate-600">
                      {formatMoney(b.unit_cost, fmt)}
                    </td>
                    <td className="px-6 py-3 text-slate-600">
                      {b.vendor_name ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Formularios de operación */}
      <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        {admin && (
          <div className="card">
            <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-800">
              <Icon name="add" className="text-brand-500" /> Nuevo lote (ENTRY)
            </h3>
            <BatchForm supplyId={id} />
          </div>
        )}
        <div className="card">
          <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-800">
            <Icon name="box" className="text-brand-500" /> Consumo FIFO
          </h3>
          <ConsumeForm supplyId={id} role={user?.role ?? "STAFF"} />
        </div>
        {admin && (
          <div className="card">
            <h3 className="mb-3 flex items-center gap-2 font-semibold text-slate-800">
              <Icon name="reconcile" className="text-brand-500" /> Conciliar stock
            </h3>
            <ReconcileForm supplyId={id} />
          </div>
        )}
      </section>

      {/* Historial */}
      <section className="mt-8">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-slate-800">
          <Icon name="movements" className="text-brand-500" /> Historial de movimientos
        </h2>
        {movements.items.length === 0 ? (
          <div className="card text-sm text-slate-500">Sin movimientos.</div>
        ) : (
          <div className="card overflow-x-auto p-0">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-brand-100 text-left text-xs uppercase text-slate-400">
                  <th className="px-6 py-3 font-medium">Fecha</th>
                  <th className="px-6 py-3 font-medium">Tipo</th>
                  <th className="px-6 py-3 text-right font-medium">Cantidad</th>
                  <th className="px-6 py-3 text-right font-medium">Stock</th>
                  <th className="px-6 py-3 font-medium">Usuario</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-50">
                {movements.items.map((m) => (
                  <tr key={m.movement_id} className="hover:bg-brand-50/40">
                    <td className="px-6 py-3 text-slate-500">
                      {formatDateTime(m.created_at)}
                    </td>
                    <td className="px-6 py-3">
                      <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">
                        {MOVEMENT_LABELS[m.movement_type]}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-right text-slate-800">
                      {formatQuantity(m.quantity, fmt)}
                    </td>
                    <td className="px-6 py-3 text-right text-slate-500">
                      {formatQuantity(m.stock_before, fmt)} → {formatQuantity(m.stock_after, fmt)}
                    </td>
                    <td className="px-6 py-3 text-slate-600">{m.user_email}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* `mpage`, no `page`: la vista podría paginar también los lotes. */}
        <Pagination
          page={movements.page}
          limit={movements.limit}
          total={movements.total}
          basePath={`/supplies/${id}`}
          param="mpage"
          noun="movimientos"
        />
      </section>
    </>
  );
}
