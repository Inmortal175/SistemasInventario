import { redirect } from "next/navigation";

import { Icon } from "@/components/Icon";
import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { isAdmin } from "@/lib/labels";
import { getSessionUser } from "@/lib/session";

export default async function ReportsPage() {
  const user = await getSessionUser();
  if (!user || !isAdmin(user.role)) redirect("/dashboard");

  return (
    <>
      <PageHeader
        title="Reportes"
        subtitle="Exportación desnormalizada lista para ETL / OLAP (PowerBI, ClickHouse)"
      />

      <InfoBanner>
        Descarga el historial completo de movimientos en un CSV plano (un registro por
        movimiento, con insumo, categoría, ubicación y usuario ya unidos), listo para
        cargarlo en PowerBI o un almacén de datos.
      </InfoBanner>

      <div className="card max-w-xl">
        <h2 className="flex items-center gap-2 font-semibold text-slate-800">
          <Icon name="reports" className="text-brand-500" /> Historial de movimientos (CSV)
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Genera un archivo plano con el JOIN de movimientos, insumos, categorías,
          ubicaciones y usuarios. Opcionalmente filtra desde una fecha.
        </p>

        {/* GET a un route handler que adjunta el token y devuelve el CSV como descarga */}
        <form
          action="/api/reports/export"
          method="get"
          className="mt-4 flex flex-wrap items-end gap-3"
        >
          <div>
            <label htmlFor="start_date" className="label">Desde (opcional)</label>
            <input id="start_date" name="start_date" type="date" className="input" />
          </div>
          <button type="submit" className="btn-primary">
            <Icon name="reports" /> Descargar CSV
          </button>
        </form>
      </div>
    </>
  );
}
