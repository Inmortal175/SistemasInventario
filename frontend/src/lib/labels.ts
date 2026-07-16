// Etiquetas en español para los enums del dominio y helpers de presentación.

import { formatQuantity } from "./format";
import type { FormatConfig } from "./format";
import type {
  LocationType,
  MovementType,
  UnitMeasure,
  UserRole,
} from "./types";

export const MOVEMENT_LABELS: Record<MovementType, string> = {
  ENTRY: "Ingreso",
  EXIT: "Salida",
  ADJUSTMENT_ADD: "Ajuste (+)",
  ADJUSTMENT_SUB: "Ajuste (−)",
  WASTE: "Merma",
  TRANSFER: "Traslado",
};

export const UNIT_LABELS: Record<UnitMeasure, string> = {
  KG: "Kilogramos",
  GR: "Gramos",
  L: "Litros",
  ML: "Mililitros",
  UNIT: "Unidad",
  PKG: "Paquete",
  BOX: "Caja",
  DOZEN: "Docena",
};

// Abreviatura compacta para tablas/listas donde el nombre completo estorba.
export const UNIT_ABBR: Record<UnitMeasure, string> = {
  KG: "kg",
  GR: "g",
  L: "L",
  ML: "ml",
  UNIT: "u",
  PKG: "paq",
  BOX: "caja",
  DOZEN: "doc",
};

export const LOCATION_TYPE_LABELS: Record<LocationType, string> = {
  SHELF: "Estante",
  REFRIGERATOR: "Refrigeradora",
  FREEZER: "Congeladora",
  CABINET: "Armario",
  COUNTER: "Mostrador",
  WAREHOUSE: "Almacén",
};

export const ROLE_LABELS: Record<UserRole, string> = {
  SUPERADMIN: "Superadmin",
  ADMIN: "Administrador",
  STAFF: "Personal",
};

// Etiqueta legible para el tipo de acción del historial de auditoría.
const ACTION_LABELS: Record<string, string> = {
  CATEGORY_CREATED: "Categoría creada",
  LOCATION_CREATED: "Ubicación creada",
  MOVEMENT_ENTRY: "Ingreso",
  MOVEMENT_EXIT: "Salida",
  MOVEMENT_WASTE: "Merma",
  MOVEMENT_ADJUSTMENT_ADD: "Ajuste (+)",
  MOVEMENT_ADJUSTMENT_SUB: "Ajuste (−)",
  MOVEMENT_TRANSFER: "Traslado",
};

export function actionLabel(actionType: string): string {
  return ACTION_LABELS[actionType] ?? actionType;
}

// Movimientos que cada rol puede registrar (espejo de ALLOWED_MOVEMENTS_BY_ROLE).
export const MOVEMENTS_BY_ROLE: Record<UserRole, MovementType[]> = {
  STAFF: ["EXIT", "WASTE"],
  ADMIN: [
    "ENTRY",
    "EXIT",
    "ADJUSTMENT_ADD",
    "ADJUSTMENT_SUB",
    "WASTE",
    "TRANSFER",
  ],
  SUPERADMIN: [
    "ENTRY",
    "EXIT",
    "ADJUSTMENT_ADD",
    "ADJUSTMENT_SUB",
    "WASTE",
    "TRANSFER",
  ],
};

export function isAdmin(role: UserRole): boolean {
  return role === "ADMIN" || role === "SUPERADMIN";
}

// Viven en ./format porque ahora dependen de los ajustes (moneda y locale).
// Se re-exportan aquí para no romper los imports existentes.
export { formatMoney, formatQuantity } from "./format";
export type { FormatConfig } from "./format";

// Cantidad + unidad abreviada, ej. "0,25 kg". Evita el "¿0,25 de qué?".
export function formatQuantityUnit(
  value: string,
  unit: UnitMeasure,
  config?: FormatConfig,
): string {
  return `${formatQuantity(value, config)} ${UNIT_ABBR[unit]}`;
}

// El backend sirve los avatares en <origin>/static/... (fuera de /api/v1).
export function assetUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  const origin = api.replace(/\/api\/v1\/?$/, "");
  return `${origin}${path}`;
}

export function formatDate(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("es-PE", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("es-PE", {
    dateStyle: "short",
    timeStyle: "short",
  });
}
