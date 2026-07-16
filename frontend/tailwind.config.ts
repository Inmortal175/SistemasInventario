import type { Config } from "tailwindcss";

const SHADES = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900] as const;

// Los tonos se resuelven en tiempo de ejecución desde variables CSS (definidas
// por paleta en globals.css), no en tiempo de compilación: así el tema puede
// cambiarse sin recompilar Tailwind. El formato "R G B" es obligatorio para que
// <alpha-value> siga funcionando en clases como bg-brand-50/40.
const brand = Object.fromEntries(
  SHADES.map((shade) => [shade, `rgb(var(--brand-${shade}) / <alpha-value>)`]),
);

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: { brand },
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica",
          "Arial",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
