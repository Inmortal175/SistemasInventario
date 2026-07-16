import Link from "next/link";
import { redirect } from "next/navigation";

import { PageHeader } from "@/components/PageHeader";
import { isAdmin } from "@/lib/labels";
import { getCategories, getLocations } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { SupplyForm } from "./SupplyForm";

export default async function NewSupplyPage() {
  const user = await getSessionUser();
  if (!user || !isAdmin(user.role)) redirect("/supplies");

  const [categories, locations] = await Promise.all([
    getCategories(),
    getLocations(),
  ]);

  if (categories.items.length === 0 || locations.items.length === 0) {
    return (
      <>
        <PageHeader title="Nuevo insumo" />
        <div className="card text-sm text-slate-600">
          Primero necesitas al menos una{" "}
          <Link href="/categories" className="font-medium text-brand-600">
            categoría
          </Link>{" "}
          y una{" "}
          <Link href="/locations" className="font-medium text-brand-600">
            ubicación
          </Link>{" "}
          activas.
        </div>
      </>
    );
  }

  return (
    <>
      <PageHeader title="Nuevo insumo" subtitle="Alta de un insumo en el inventario" />
      <div className="card">
        <SupplyForm categories={categories.items} locations={locations.items} />
      </div>
    </>
  );
}
