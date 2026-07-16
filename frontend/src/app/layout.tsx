import type { Metadata } from "next";

import { assetUrl } from "@/lib/labels";
import { getSettings } from "@/lib/queries";

import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const settings = await getSettings();
  const logo = assetUrl(settings.logo_url);

  return {
    title: settings.app_name,
    description: "Gestión de inventario para pastelerías",
    // El logo ya se guarda cuadrado, así que sirve tal cual de favicon. Sin
    // logo cae al emblema por defecto en /icon.svg.
    icons: { icon: logo ?? "/icon.svg" },
  };
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const settings = await getSettings();

  // `data-theme` selecciona la paleta de variables CSS definida en globals.css.
  return (
    <html lang="es" data-theme={settings.theme}>
      <body>{children}</body>
    </html>
  );
}
