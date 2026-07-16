"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon, type IconName } from "@/components/Icon";
import type { UserRole } from "@/lib/types";

interface NavItem {
  href: string;
  label: string;
  icon: IconName;
  roles?: UserRole[]; // si se omite, visible para todos los roles
}

const NAV: NavItem[] = [
  { href: "/dashboard", label: "Resumen", icon: "dashboard" },
  { href: "/supplies", label: "Insumos", icon: "supplies" },
  { href: "/products", label: "Productos", icon: "products" },
  { href: "/movements", label: "Movimientos", icon: "movements" },
  { href: "/production", label: "Producción", icon: "production" },
  { href: "/categories", label: "Categorías", icon: "categories" },
  { href: "/locations", label: "Ubicaciones", icon: "locations" },
  { href: "/reports", label: "Reportes", icon: "reports", roles: ["ADMIN", "SUPERADMIN"] },
  { href: "/users", label: "Usuarios", icon: "users", roles: ["SUPERADMIN"] },
  { href: "/settings", label: "Ajustes", icon: "settings", roles: ["SUPERADMIN"] },
];

export function Sidebar({ role }: { role: UserRole }) {
  const pathname = usePathname();
  const items = NAV.filter((item) => !item.roles || item.roles.includes(role));

  return (
    <nav className="space-y-1">
      {items.map((item) => {
        const active =
          pathname === item.href || pathname.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
              active
                ? "bg-brand-500 text-white"
                : "text-slate-600 hover:bg-brand-100"
            }`}
          >
            <Icon name={item.icon} fixedWidth />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
