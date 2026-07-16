import type { ThemeName } from "./types";

/** Muestras para la vista previa del selector. Los valores reales de cada tono
 *  viven en globals.css; aquí solo se replican tres para pintar el swatch. */
export const THEMES: {
  value: ThemeName;
  label: string;
  swatch: [string, string, string];
}[] = [
  { value: "rosa", label: "Rosa pastel", swatch: ["#ffe4ee", "#ff6b9d", "#bd0f50"] },
  { value: "chocolate", label: "Chocolate", swatch: ["#f7ebe0", "#ba7c47", "#653f1e"] },
  { value: "menta", label: "Menta", swatch: ["#d9f9ec", "#34cd9d", "#0b6650"] },
  { value: "azul", label: "Azul", swatch: ["#dbeafe", "#60a5fa", "#1e40af"] },
];
