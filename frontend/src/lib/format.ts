import type { SystemSettings } from "./types";

/** Moneda y locale son ajustes globales, pero se pasan explícitamente en vez de
 *  guardarlos en un módulo mutable: en el servidor ese estado se compartiría
 *  entre peticiones concurrentes. */
export interface FormatConfig {
  locale: string;
  currency: string;
}

export function formatConfig(settings: SystemSettings): FormatConfig {
  return { locale: settings.locale, currency: settings.currency_code };
}

export const DEFAULT_FORMAT: FormatConfig = { locale: "es-PE", currency: "PEN" };

export function formatQuantity(value: string, config: FormatConfig = DEFAULT_FORMAT): string {
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  return n.toLocaleString(config.locale, { maximumFractionDigits: 3 });
}

export function formatMoney(value: string, config: FormatConfig = DEFAULT_FORMAT): string {
  const n = Number(value);
  if (Number.isNaN(n)) return value;
  try {
    return n.toLocaleString(config.locale, {
      style: "currency",
      currency: config.currency,
      minimumFractionDigits: 2,
    });
  } catch {
    // Un código de moneda que Intl no conoce no debe romper la página entera.
    return `${config.currency} ${n.toFixed(2)}`;
  }
}
