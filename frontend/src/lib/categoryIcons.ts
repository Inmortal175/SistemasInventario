import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faAppleWhole,
  faBacon,
  faBlender,
  faBottleWater,
  faBowlFood,
  faBoxOpen,
  faBreadSlice,
  faBroom,
  faCakeCandles,
  faCandyCane,
  faCarrot,
  faCheese,
  faCookieBite,
  faDrumstickBite,
  faEgg,
  faFire,
  faFish,
  faGlassWater,
  faHeart,
  faIceCream,
  faJar,
  faKitchenSet,
  faLeaf,
  faLemon,
  faMugHot,
  faPepperHot,
  faPizzaSlice,
  faScaleBalanced,
  faScrewdriverWrench,
  faSeedling,
  faSnowflake,
  faSoap,
  faSprayCanSparkles,
  faStar,
  faTag,
  faUtensils,
  faWheatAwn,
  faWineBottle,
} from "@fortawesome/free-solid-svg-icons";

// Espejo de ALLOWED_CATEGORY_ICONS en backend/app/domain/category_icons.py.
// Si agregas uno aquí, agrégalo allá o la API rechazará la categoría.
export const CATEGORY_ICONS: Record<string, IconDefinition> = {
  cake: faCakeCandles,
  cookie: faCookieBite,
  bread: faBreadSlice,
  wheat: faWheatAwn,
  "ice-cream": faIceCream,
  candy: faCandyCane,

  cheese: faCheese,
  egg: faEgg,
  milk: faGlassWater,
  meat: faDrumstickBite,
  bacon: faBacon,
  fish: faFish,

  apple: faAppleWhole,
  lemon: faLemon,
  carrot: faCarrot,
  pepper: faPepperHot,
  seedling: faSeedling,
  leaf: faLeaf,

  mug: faMugHot,
  bottle: faBottleWater,
  wine: faWineBottle,
  jar: faJar,
  bowl: faBowlFood,
  pizza: faPizzaSlice,

  utensils: faUtensils,
  kitchen: faKitchenSet,
  blender: faBlender,
  scale: faScaleBalanced,
  fire: faFire,
  snowflake: faSnowflake,

  box: faBoxOpen,
  broom: faBroom,
  soap: faSoap,
  spray: faSprayCanSparkles,
  tools: faScrewdriverWrench,

  tag: faTag,
  star: faStar,
  heart: faHeart,
};

export type CategoryIconName = keyof typeof CATEGORY_ICONS;

export const CATEGORY_ICON_GROUPS: { label: string; icons: string[] }[] = [
  { label: "Pastelería", icons: ["cake", "cookie", "bread", "wheat", "ice-cream", "candy"] },
  { label: "Lácteos y proteínas", icons: ["cheese", "egg", "milk", "meat", "bacon", "fish"] },
  { label: "Frutas y verduras", icons: ["apple", "lemon", "carrot", "pepper", "seedling", "leaf"] },
  { label: "Bebidas y envases", icons: ["mug", "bottle", "wine", "jar", "bowl", "pizza"] },
  { label: "Cocina", icons: ["utensils", "kitchen", "blender", "scale", "fire", "snowflake"] },
  { label: "Almacén y limpieza", icons: ["box", "broom", "soap", "spray", "tools"] },
  { label: "Generales", icons: ["tag", "star", "heart"] },
];

export function isCategoryIcon(name: string | null | undefined): boolean {
  return Boolean(name && name in CATEGORY_ICONS);
}
