import { Footer } from "@/components/Footer";
import { assetUrl } from "@/lib/labels";
import { getSettings } from "@/lib/queries";

import { LoginForm } from "./LoginForm";

export default async function LoginPage() {
  const settings = await getSettings();
  const logo = assetUrl(settings.logo_url);

  // Cadena de respaldo: cada tamaño cae al inmediatamente mayor, de modo que
  // subir una sola imagen (la de escritorio) ya cubre los tres dispositivos.
  const desktop = assetUrl(settings.login_bg_desktop_url);
  const tablet = assetUrl(settings.login_bg_tablet_url) ?? desktop;
  const mobile = assetUrl(settings.login_bg_mobile_url) ?? tablet;
  const hasBackground = Boolean(mobile);

  return (
    <div className="relative flex min-h-screen flex-col">
      {/* Apilamiento local: un z negativo quedaría detrás del color de fondo
          que el <body> propaga al lienzo. */}
      {hasBackground && (
        <div className="absolute inset-0 overflow-hidden" aria-hidden>
          <picture>
            {desktop && <source media="(min-width: 1024px)" srcSet={desktop} />}
            {tablet && <source media="(min-width: 768px)" srcSet={tablet} />}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={mobile!} alt="" className="h-full w-full object-cover" />
          </picture>
          {/* Velo: garantiza contraste sea cual sea la foto que suban. La
              opacidad es un ajuste, así que va en style y no en una clase de
              Tailwind (que se compila estáticamente). */}
          <div
            className="absolute inset-0 bg-slate-900"
            style={{ opacity: settings.login_overlay_opacity / 100 }}
          />
        </div>
      )}

      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">
          <div className="mb-8 text-center">
            {logo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={logo}
                alt={settings.app_name}
                className="mx-auto mb-3 h-20 w-20 rounded-2xl object-contain"
              />
            ) : (
              <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500 text-2xl">
                🧁
              </div>
            )}
            <h1
              className={`text-2xl font-bold ${
                hasBackground ? "text-white drop-shadow" : "text-slate-800"
              }`}
            >
              {settings.app_name}
            </h1>
            <p
              className={`mt-1 text-sm ${
                hasBackground ? "text-white/80" : "text-slate-500"
              }`}
            >
              Ingresa para gestionar tu inventario
            </p>
          </div>

          <div className="card">
            <LoginForm />
          </div>
        </div>
      </main>

      <div className="relative z-10">
        <Footer appName={settings.app_name} onImage={hasBackground} />
      </div>
    </div>
  );
}
