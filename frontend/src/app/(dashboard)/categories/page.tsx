import { CategoryIcon } from "@/components/CategoryIcon";
import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { isAdmin } from "@/lib/labels";
import { getCategories } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { CategoryForm } from "./CategoryForm";

export default async function CategoriesPage() {
  const [categories, user] = await Promise.all([
    getCategories(),
    getSessionUser(),
  ]);
  const canManage = user ? isAdmin(user.role) : false;

  return (
    <>
      <PageHeader
        title="Categorías"
        subtitle={`${categories.total} activas`}
      />

      <InfoBanner>
        Clasifica los insumos con categorías propias (nombre, color e ícono) sin tocar el
        código. Se usan para filtrar y agrupar el inventario. Crear categorías es solo
        para administradores.
      </InfoBanner>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          {categories.items.length === 0 ? (
            <div className="card text-sm text-slate-500">
              Aún no hay categorías.
            </div>
          ) : (
            <div className="card divide-y divide-brand-50 p-0">
              {categories.items.map((c) => (
                <div key={c.id} className="flex items-center gap-3 px-6 py-4">
                  <span
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-white"
                    style={{ backgroundColor: c.color_hex }}
                    aria-hidden
                  >
                    <CategoryIcon name={c.icon_name} />
                  </span>
                  <div className="min-w-0">
                    <p className="font-medium text-slate-800">{c.name}</p>
                    {c.description && (
                      <p className="truncate text-xs text-slate-400">
                        {c.description}
                      </p>
                    )}
                  </div>
                  <span className="ml-auto font-mono text-xs text-slate-400">
                    {c.color_hex}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {canManage && (
          <div className="card h-fit">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">
              Nueva categoría
            </h2>
            <CategoryForm />
          </div>
        )}
      </div>
    </>
  );
}
