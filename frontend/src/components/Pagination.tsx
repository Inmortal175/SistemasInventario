import Link from "next/link";

interface Props {
  page: number;
  limit: number;
  total: number;
  /** Ruta sin query, p. ej. "/supplies". */
  basePath: string;
  /** Nombre del parámetro de página. Permite dos paginadores en una misma vista. */
  param?: string;
  /** Otros parámetros de la URL que deben sobrevivir al cambio de página. */
  query?: Record<string, string | undefined>;
  /** Cómo nombrar lo que se lista, para el resumen. */
  noun?: string;
}

/** Ventana de páginas alrededor de la actual, con elipsis. Siempre muestra la
 *  primera y la última para que se pueda saltar a los extremos de un tirón. */
function pageWindow(page: number, pages: number): (number | "…")[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, i) => i + 1);

  const around = [page - 1, page, page + 1].filter((p) => p > 1 && p < pages);
  const items: (number | "…")[] = [1];
  if (around[0] > 2) items.push("…");
  items.push(...around);
  if (around[around.length - 1] < pages - 1) items.push("…");
  items.push(pages);
  return items;
}

export function Pagination({
  page,
  limit,
  total,
  basePath,
  param = "page",
  query = {},
  noun = "registros",
}: Props) {
  const pages = Math.max(1, Math.ceil(total / limit));
  if (pages <= 1) return null;

  const current = Math.min(Math.max(page, 1), pages);
  const first = (current - 1) * limit + 1;
  const last = Math.min(current * limit, total);

  const href = (target: number) => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value) params.set(key, value);
    }
    if (target > 1) params.set(param, String(target));
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  const arrow = (target: number, label: string, disabled: boolean) =>
    disabled ? (
      <span className="cursor-not-allowed rounded-lg px-3 py-1.5 text-xs font-medium text-slate-300">
        {label}
      </span>
    ) : (
      <Link
        href={href(target)}
        scroll={false}
        className="rounded-lg px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-brand-100"
      >
        {label}
      </Link>
    );

  return (
    <nav
      aria-label="Paginación"
      className="mt-4 flex flex-col items-center justify-between gap-3 sm:flex-row"
    >
      <p className="text-xs text-slate-400">
        Mostrando {first}–{last} de {total} {noun}
      </p>

      <div className="flex items-center gap-1">
        {arrow(current - 1, "← Anterior", current === 1)}

        {pageWindow(current, pages).map((item, i) =>
          item === "…" ? (
            <span key={`gap-${i}`} className="px-2 text-xs text-slate-300">
              …
            </span>
          ) : (
            <Link
              key={item}
              href={href(item)}
              scroll={false}
              aria-current={item === current ? "page" : undefined}
              className={`min-w-8 rounded-lg px-2.5 py-1.5 text-center text-xs font-medium transition ${
                item === current
                  ? "bg-brand-500 text-white"
                  : "text-slate-600 hover:bg-brand-100"
              }`}
            >
              {item}
            </Link>
          ),
        )}

        {arrow(current + 1, "Siguiente →", current === pages)}
      </div>
    </nav>
  );
}
