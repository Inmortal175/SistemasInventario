import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

import { CATEGORY_ICONS } from "@/lib/categoryIcons";

/** Devuelve null si el slug no está en el registro: una categoría antigua con un
 *  ícono retirado debe degradar al color plano, no romper la página. */
export function CategoryIcon({
  name,
  className,
}: {
  name: string | null | undefined;
  className?: string;
}) {
  if (!name) return null;
  const icon = CATEGORY_ICONS[name];
  if (!icon) return null;
  return <FontAwesomeIcon icon={icon} className={className} />;
}
