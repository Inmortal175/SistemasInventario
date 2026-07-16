import { redirect } from "next/navigation";

import { InfoBanner } from "@/components/InfoBanner";
import { PageHeader } from "@/components/PageHeader";
import { getSettings } from "@/lib/queries";
import { getSessionUser } from "@/lib/session";

import { BrandingForm } from "./BrandingForm";
import { BusinessForm } from "./BusinessForm";
import { LoginBackgroundForm } from "./LoginBackgroundForm";
import { LogoForm } from "./LogoForm";
import { OperationForm } from "./OperationForm";

export default async function SettingsPage() {
  const me = await getSessionUser();
  if (!me || me.role !== "SUPERADMIN") redirect("/dashboard");

  const settings = await getSettings();
  const hasBackground = Boolean(
    settings.login_bg_mobile_url ??
      settings.login_bg_tablet_url ??
      settings.login_bg_desktop_url,
  );

  return (
    <>
      <PageHeader
        title="Ajustes"
        subtitle="Configuración global del sistema (solo Superadmin)"
      />

      <InfoBanner>
        Todo lo de esta página es <strong>global</strong>: afecta a todos los usuarios,
        no solo a tu cuenta. Los cambios de marca y de operación se aplican al instante.
      </InfoBanner>

      <div className="space-y-6">
        <section className="card">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">Logo</h2>
          <LogoForm currentLogo={settings.logo_url} />
        </section>

        <section className="card">
          <h2 className="mb-1 text-sm font-semibold text-slate-700">
            Fondo del login
          </h2>
          <p className="mb-4 text-xs text-slate-400">
            Una imagen por dispositivo, cada una con su propio recorte.
          </p>
          <LoginBackgroundForm settings={settings} />
        </section>

        <section className="card">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">
            Nombre, tema y velo
          </h2>
          <BrandingForm
            appName={settings.app_name}
            theme={settings.theme}
            overlayOpacity={settings.login_overlay_opacity}
            hasBackground={hasBackground}
          />
        </section>

        <section className="card">
          <h2 className="mb-1 text-sm font-semibold text-slate-700">Operación</h2>
          <p className="mb-4 text-xs text-slate-400">
            Reglas del día a día: alertas de vencimiento, moneda y paginación.
          </p>
          <OperationForm settings={settings} />
        </section>

        <section className="card">
          <h2 className="mb-1 text-sm font-semibold text-slate-700">
            Datos de la pastelería
          </h2>
          <p className="mb-4 text-xs text-slate-400">
            Identidad fiscal, para futuros membretes en reportes.
          </p>
          <BusinessForm settings={settings} />
        </section>
      </div>
    </>
  );
}
