"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="card">
      <h2 className="text-lg font-semibold text-slate-800">
        Ocurrió un problema
      </h2>
      <p className="mt-1 text-sm text-slate-500">
        No se pudieron cargar los datos. Verifica que el backend esté activo e
        inténtalo de nuevo.
      </p>
      <p className="mt-2 text-xs text-slate-400">{error.message}</p>
      <button onClick={reset} className="btn-primary mt-4">
        Reintentar
      </button>
    </div>
  );
}
