import { Icon } from "@/components/Icon";

// Explicación breve de cada módulo para que la UI sea autoexplicativa.
export function InfoBanner({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-6 flex items-start gap-3 rounded-xl border border-brand-100 bg-brand-50/60 px-4 py-3 text-sm text-slate-600">
      <span className="mt-0.5 text-brand-500">
        <Icon name="info" />
      </span>
      <p>{children}</p>
    </div>
  );
}
