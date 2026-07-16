import Link from "next/link";

import { Icon, type IconName } from "@/components/Icon";
import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { formatConfig } from "@/lib/format";
import { formatMoney, formatQuantity, isAdmin, UNIT_LABELS } from "@/lib/labels";
import {
  getCategories,
  getFinancials,
  getKpis,
  getLocations,
  getSettings,
  getSupplies,
} from "@/lib/queries";
import { getSessionUser } from "@/lib/session";
import type { FinancialsResponse, KpisResponse } from "@/lib/types";

function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: number | string;
  icon: IconName;
  accent?: boolean;
}) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">{label}</p>
        <span
          className={`text-lg ${accent ? "text-red-400" : "text-brand-400"}`}
        >
          <Icon name={icon} />
        </span>
      </div>
      <p
        className={`mt-1 text-3xl font-bold ${
          accent ? "text-red-600" : "text-slate-800"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

export default async function DashboardPage() {
  const user = await getSessionUser();
  const admin = user ? isAdmin(user.role) : false;

  const [supplies, categories, locations, settings] = await Promise.all([
    getSupplies({ limit: 100 }),
    getCategories(),
    getLocations(),
    getSettings(),
  ]);
  const fmt = formatConfig(settings);

  // KPIs y valorización son ADMIN+; para STAFF quedan en null.
  let kpis: KpisResponse | null = null;
  let financials: FinancialsResponse | null = null;
  if (admin) {
    [kpis, financials] = await Promise.all([
      getKpis().catch(() => null),
      getFinancials().catch(() => null),
    ]);
  }

  const lowStock = supplies.items.filter((s) => s.is_below_minimum);

  return (
    <>
      <PageHeader title="Resumen" subtitle="Estado general del inventario" />

      <InfoBanner>
        Vista general del inventario: insumos activos, cuántos están bajo su stock
        mínimo y, para administradores, los movimientos de las últimas 24 h, el valor
        financiero del almacén y las mermas del periodo.
      </InfoBanner>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Insumos activos" value={supplies.total} icon="supplies" />
        <StatCard
          label="Bajo mínimo"
          value={kpis?.total_critical_items ?? supplies.low_stock_count}
          icon="alert"
          accent={(kpis?.total_critical_items ?? supplies.low_stock_count) > 0}
        />
        <StatCard label="Categorías" value={categories.total} icon="categories" />
        <StatCard label="Ubicaciones" value={locations.total} icon="locations" />
      </div>

      {admin && (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <StatCard
            label="Movimientos (24 h)"
            value={kpis?.movements_last_24h ?? 0}
            icon="movements"
          />
          <StatCard
            label="Valor activo del almacén"
            value={formatMoney(financials?.total_active_value ?? "0", fmt)}
            icon="financials"
          />
          <StatCard
            label="Pérdida por mermas"
            value={formatMoney(financials?.total_waste_loss ?? "0", fmt)}
            icon="reconcile"
            accent={Number(financials?.total_waste_loss ?? 0) > 0}
          />
        </div>
      )}

      <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800">
              Insumos bajo el mínimo
            </h2>
            <Link
              href="/supplies"
              className="text-sm font-medium text-brand-600"
            >
              Ver todos →
            </Link>
          </div>

          {lowStock.length === 0 ? (
            <div className="card flex items-center gap-2 text-sm text-slate-500">
              <Icon name="ok" className="text-emerald-500" />
              Todo en orden: ningún insumo bajo el mínimo.
            </div>
          ) : (
            <div className="card divide-y divide-brand-50 p-0">
              {lowStock.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between px-6 py-4"
                >
                  <div>
                    <p className="font-medium text-slate-800">{s.name}</p>
                    <p className="text-xs text-slate-400">SKU {s.sku}</p>
                  </div>
                  <div className="text-right text-sm">
                    <p className="font-semibold text-red-600">
                      {formatQuantity(s.current_stock, fmt)}{" "}
                      <span className="text-xs font-normal text-slate-400">
                        / mín {formatQuantity(s.minimum_stock, fmt)}
                      </span>
                    </p>
                    <p className="text-xs text-slate-400">
                      {UNIT_LABELS[s.unit_of_measure]}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {admin && (
          <div>
            <h2 className="mb-3 text-lg font-semibold text-slate-800">
              Top insumos con mermas
            </h2>
            {!kpis || kpis.top_wasted_supplies.length === 0 ? (
              <div className="card text-sm text-slate-500">
                Sin mermas registradas.
              </div>
            ) : (
              <div className="card divide-y divide-brand-50 p-0">
                {kpis.top_wasted_supplies.map((w) => (
                  <div
                    key={w.supply_id}
                    className="flex items-center justify-between px-6 py-4"
                  >
                    <p className="font-medium text-slate-800">
                      {w.supply_name}
                    </p>
                    <p className="text-sm font-semibold text-amber-600">
                      {formatQuantity(w.total_wasted, fmt)}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>
    </>
  );
}
