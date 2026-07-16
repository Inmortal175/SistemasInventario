import Link from "next/link";
import { redirect } from "next/navigation";

import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { Pagination } from "@/components/Pagination";
import { formatConfig } from "@/lib/format";
import { formatQuantity, UNIT_LABELS } from "@/lib/labels";
import { getLocations, getSettings, getSupplies } from "@/lib/queries";

export default async function ProductsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: rawPage } = await searchParams;
  const page = Math.max(1, Number(rawPage) || 1);

  const settings = await getSettings();
  const fmt = formatConfig(settings);

  const [products, locations] = await Promise.all([
    getSupplies({ page, limit: settings.page_size, item_type: "FINISHED_PRODUCT" }),
    getLocations(),
  ]);

  if (page > 1 && products.items.length === 0 && products.total > 0) {
    redirect("/products");
  }

  const locationCode = new Map(locations.items.map((l) => [l.id, l.code]));

  return (
    <>
      <PageHeader
        title="Productos terminados"
        subtitle={`${products.total} producto(s) · elaborados por receta`}
      />

      <InfoBanner>
        Aquí viven los productos que la pastelería <strong>produce y guarda</strong> (p. ej.
        tortas en refrigeración) para vender después. Se crean automáticamente al definir una
        receta con producto; al producir sube su stock, y al venderlos se descuenta por FIFO
        (primero lo más próximo a vencer). Para producir, ve a{" "}
        <Link href="/production" className="text-brand-600 underline">Producción</Link>.
      </InfoBanner>

      {products.items.length === 0 ? (
        <div className="card text-sm text-slate-500">
          Aún no hay productos terminados. Crea una receta con producto en{" "}
          <Link href="/production" className="text-brand-600 underline">Producción</Link>.
        </div>
      ) : (
        <div className="card overflow-x-auto p-0">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-brand-100 text-left text-xs uppercase text-slate-400">
                <th className="px-6 py-3 font-medium">Producto</th>
                <th className="px-6 py-3 font-medium">Ubicación</th>
                <th className="px-6 py-3 text-right font-medium">En stock</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-50">
              {products.items.map((p) => (
                <tr key={p.id} className="hover:bg-brand-50/40">
                  <td className="px-6 py-3">
                    <Link
                      href={`/supplies/${p.id}`}
                      className="font-medium text-slate-800 hover:text-brand-600 hover:underline"
                    >
                      {p.name}
                    </Link>
                    <span className="block text-xs text-slate-400">SKU {p.sku}</span>
                  </td>
                  <td className="px-6 py-3 text-slate-600">
                    {locationCode.get(p.location_id) ?? "—"}
                  </td>
                  <td className="px-6 py-3 text-right font-medium text-slate-800">
                    {formatQuantity(p.current_stock, fmt)}{" "}
                    <span className="text-xs text-slate-400">
                      {UNIT_LABELS[p.unit_of_measure]}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Pagination
        page={products.page}
        limit={products.limit}
        total={products.total}
        basePath="/products"
        noun="productos"
      />
    </>
  );
}
