import { config, type IconProp } from "@fortawesome/fontawesome-svg-core";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faArrowRightArrowLeft,
  faBoxesStacked,
  faCakeCandles,
  faChartLine,
  faCircleCheck,
  faCircleInfo,
  faTriangleExclamation,
  faFileCsv,
  faFlask,
  faLayerGroup,
  faLocationDot,
  faMoneyBillWave,
  faRightFromBracket,
  faScaleBalanced,
  faTag,
  faUsersGear,
  faIndustry,
  faPlus,
  faBoxOpen,
  faBars,
  faXmark,
  faGear,
  faImage,
  faEye,
  faEyeSlash,
} from "@fortawesome/free-solid-svg-icons";

import "@fortawesome/fontawesome-svg-core/styles.css";

// El CSS se importa manualmente arriba; evitamos que FA lo inyecte por su cuenta
// (rompe SSR en el App Router de Next).
config.autoAddCss = false;

// Registro nombrado de iconos: mantiene los imports de icon packs en un solo lugar
// y permite referenciarlos por clave desde componentes de servidor y cliente.
export const ICONS = {
  dashboard: faChartLine,
  supplies: faBoxesStacked,
  movements: faArrowRightArrowLeft,
  categories: faTag,
  locations: faLocationDot,
  production: faIndustry,
  products: faCakeCandles,
  recipes: faFlask,
  users: faUsersGear,
  reports: faFileCsv,
  financials: faMoneyBillWave,
  batches: faLayerGroup,
  reconcile: faScaleBalanced,
  logout: faRightFromBracket,
  brand: faCakeCandles,
  ok: faCircleCheck,
  info: faCircleInfo,
  alert: faTriangleExclamation,
  add: faPlus,
  box: faBoxOpen,
  menu: faBars,
  close: faXmark,
  settings: faGear,
  image: faImage,
  eye: faEye,
  eyeSlash: faEyeSlash,
} as const;

export type IconName = keyof typeof ICONS;

export function Icon({
  name,
  className,
  fixedWidth = false,
}: {
  name: IconName;
  className?: string;
  fixedWidth?: boolean;
}) {
  return (
    <FontAwesomeIcon
      icon={ICONS[name] as IconProp}
      className={className}
      fixedWidth={fixedWidth}
    />
  );
}
