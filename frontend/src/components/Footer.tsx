const AUTHOR = "Franklin Figueroa Pérez";

/** `onImage` aclara el texto cuando el pie va sobre una foto de fondo. */
export function Footer({
  appName,
  onImage = false,
}: {
  appName: string;
  onImage?: boolean;
}) {
  // Se calcula en el servidor, en cada render: escribirlo a mano lo dejaría
  // desfasado en enero.
  const year = new Date().getFullYear();

  return (
    <footer
      className={`px-4 py-5 sm:px-5 md:px-10 ${
        onImage ? "" : "border-t border-brand-100"
      }`}
    >
      <div
        className={`mx-auto flex max-w-6xl flex-col items-center gap-1 text-center text-xs sm:flex-row sm:justify-between sm:text-left ${
          onImage ? "text-white/70 drop-shadow" : "text-slate-400"
        }`}
      >
        <p>
          © {year} {AUTHOR}. Todos los derechos reservados.
        </p>
        <p>{appName}</p>
      </div>
    </footer>
  );
}
