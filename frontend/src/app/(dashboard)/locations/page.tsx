import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { isAdmin, LOCATION_TYPE_LABELS } from "@/lib/labels";
import { getLocations } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { LocationForm } from "./LocationForm";

export default async function LocationsPage() {
  const [locations, user] = await Promise.all([
    getLocations(),
    getSessionUser(),
  ]);
  const canManage = user ? isAdmin(user.role) : false;

  return (
    <>
      <PageHeader title="Ubicaciones" subtitle={`${locations.total} activas`} />

      <InfoBanner>
        Registra los lugares físicos rotulados donde se guardan los insumos (estantes,
        refrigeradoras, congeladoras…). El código sigue un formato validado, p. ej.
        <span className="font-mono"> EST-01-F2</span> o <span className="font-mono">REF-02</span>.
      </InfoBanner>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {locations.items.length === 0 ? (
            <div className="card text-sm text-slate-500">
              Aún no hay ubicaciones.
            </div>
          ) : (
            <div className="card divide-y divide-brand-50 p-0">
              {locations.items.map((l) => (
                <div key={l.id} className="flex items-center gap-3 px-6 py-4">
                  <span className="font-mono text-sm font-semibold text-brand-600">
                    {l.code}
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm text-slate-700">
                      {LOCATION_TYPE_LABELS[l.location_type]}
                    </p>
                    {l.description && (
                      <p className="truncate text-xs text-slate-400">
                        {l.description}
                      </p>
                    )}
                  </div>
                  {l.capacity_units != null && (
                    <span className="ml-auto text-xs text-slate-400">
                      cap. {l.capacity_units}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {canManage && (
          <div className="card h-fit">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">
              Nueva ubicación
            </h2>
            <LocationForm />
          </div>
        )}
      </div>
    </>
  );
}
