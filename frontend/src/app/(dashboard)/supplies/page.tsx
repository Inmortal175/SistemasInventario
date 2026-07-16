import Link from "next/link";
import { redirect } from "next/navigation";

import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { formatConfig } from "@/lib/format";
import { formatMoney, formatQuantity, isAdmin, UNIT_LABELS } from "@/lib/labels";
import {
  getCategories,
  getLocations,
  getSettings,
  getSupplies,
} from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

export default async function SuppliesPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: rawPage } = await searchParams;
  const page = Math.max(1, Number(rawPage) || 1);

  // El tamaño de página y el formato de moneda los fija el superadmin en Ajustes.
  const settings = await getSettings();
  const fmt = formatConfig(settings);

  const [supplies, categories, locations, user] = await Promise.all([
    // Solo insumos (materia prima); los productos terminados tienen su propia sección.
    getSupplies({ page, limit: settings.page_size, item_type: "INGREDIENT" }),
    getCategories(),
    getLocations(),
    getSessionUser(),
  ]);

  // Una página fuera de rango (marcador viejo, o registros borrados) mostraría
  // el vacío "aún no hay insumos". Devolvemos al inicio del listado.
  if (page > 1 && supplies.items.length === 0 && supplies.total > 0) {
    redirect("/supplies");
  }

  const categoryName = new Map(categories.items.map((c) => [c.id, c.name]));
  const locationCode = new Map(locations.items.map((l) => [l.id, l.code]));
  const canCreate = user ? isAdmin(user.role) : false;

  return (
    <>
      <PageHeader
        title="Insumos"
        subtitle={`${supplies.total} activos · ${supplies.low_stock_count} bajo mínimo`}
        action={
          canCreate ? (
            <Link href="/supplies/new" className="btn-primary">
              + Nuevo insumo
            </Link>
          ) : undefined
        }
      />

      <InfoBanner>
        Catálogo de insumos con su stock actual y costo. Haz clic en un insumo para ver
        sus lotes (orden FIFO por vencimiento), registrar entradas, consumir por FIFO o
        conciliar el stock con el conteo físico.
      </InfoBanner>

      {supplies.items.length === 0 ? (
        <div className="card text-sm text-slate-500">
          Aún no hay insumos registrados.
        </div>
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-brand-100 text-left text-xs uppercase text-slate-400">
                <th className="px-6 py-3 font-medium">Insumo</th>
                <th className="px-6 py-3 font-medium">Categoría</th>
                <th className="px-6 py-3 font-medium">Ubicación</th>
                <th className="px-6 py-3 text-right font-medium">Stock</th>
                <th className="px-6 py-3 text-right font-medium">Costo unit.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-50">
              {supplies.items.map((s) => (
                <tr key={s.id} className="hover:bg-brand-50/40">
                  <td className="px-6 py-3">
                    <div className="flex items-center gap-2">
                      <Link
                        href={`/supplies/${s.id}`}
                        className="font-medium text-slate-800 hover:text-brand-600 hover:underline"
                      >
                        {s.name}
                      </Link>
                      {s.is_below_minimum && (
                        <span className="rounded-full bg-red-100 px-2 py-0.5 text-[11px] font-semibold text-red-600">
                          bajo mínimo
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-slate-400">SKU {s.sku}</span>
                  </td>
                  <td className="px-6 py-3 text-slate-600">
                    {categoryName.get(s.category_id) ?? "—"}
                  </td>
                  <td className="px-6 py-3 text-slate-600">
                    {locationCode.get(s.location_id) ?? "—"}
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span
                      className={
                        s.is_below_minimum
                          ? "font-semibold text-red-600"
                          : "font-medium text-slate-800"
                      }
                    >
                      {formatQuantity(s.current_stock, fmt)}
                    </span>
                    <span className="text-xs text-slate-400">
                      {" "}
                      {UNIT_LABELS[s.unit_of_measure]}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-right text-slate-600">
                    {formatMoney(s.unit_cost, fmt)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination
        page={supplies.page}
        limit={supplies.limit}
        total={supplies.total}
        basePath="/supplies"
        noun="insumos"
      />
    </>
  );
}
