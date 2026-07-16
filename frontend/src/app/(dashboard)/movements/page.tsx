import { redirect } from "next/navigation";

import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { formatConfig } from "@/lib/format";
import { formatQuantity, MOVEMENTS_BY_ROLE, UNIT_LABELS } from "@/lib/labels";
import { getSettings, getSupplies } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { MovementForm } from "./MovementForm";

export default async function MovementsPage() {
  const user = await getSessionUser();
  if (!user) redirect("/login");

  const [supplies, settings] = await Promise.all([getSupplies(), getSettings()]);
  const fmt = formatConfig(settings);
  const allowed = MOVEMENTS_BY_ROLE[user.role];

  const options = supplies.items.map((s) => ({
    id: s.id,
    label: `${s.name} — ${formatQuantity(s.current_stock, fmt)} ${UNIT_LABELS[s.unit_of_measure]}`,
  }));

  return (
    <>
      <PageHeader
        title="Registrar movimiento"
        subtitle="Ingresos, salidas, mermas y ajustes de stock"
      />

      <InfoBanner>
        Registra un movimiento puntual de un insumo. El personal de cocina solo puede
        registrar salidas y mermas; los ingresos y ajustes son para administradores. El
        stock se actualiza al instante y avisa si queda bajo el mínimo.
      </InfoBanner>

      {options.length === 0 ? (
        <div className="card text-sm text-slate-500">
          No hay insumos disponibles para registrar movimientos.
        </div>
      ) : (
        <div className="card max-w-lg">
          <MovementForm supplies={options} allowedTypes={allowed} />
        </div>
      )}
    </>
  );
}
