// Tipos espejo de los schemas Pydantic del backend (app/application/schemas).

export type UserRole = "SUPERADMIN" | "ADMIN" | "STAFF";

export type MovementType =
  | "ENTRY"
  | "EXIT"
  | "ADJUSTMENT_ADD"
  | "ADJUSTMENT_SUB"
  | "WASTE"
  | "TRANSFER";

export type UnitMeasure =
  | "KG"
  | "GR"
  | "L"
  | "ML"
  | "UNIT"
  | "PKG"
  | "BOX"
  | "DOZEN";

export type LocationType =
  | "SHELF"
  | "REFRIGERATOR"
  | "FREEZER"
  | "CABINET"
  | "COUNTER"
  | "WAREHOUSE";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  full_name: string;
  role: UserRole;
  avatar_url: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  avatar_url: string | null;
  created_at: string;
}

// Espejo del enum ThemeName del backend.
export type ThemeName = "rosa" | "chocolate" | "menta" | "azul";

export type LoginBackgroundDevice = "mobile" | "tablet" | "desktop";

export interface SystemSettings {
  app_name: string;
  logo_url: string | null;
  theme: ThemeName;

  login_bg_mobile_url: string | null;
  login_bg_tablet_url: string | null;
  login_bg_desktop_url: string | null;
  login_overlay_opacity: number;

  expiration_alert_days: number;
  currency_code: string;
  locale: string;
  page_size: number;

  business_name: string | null;
  tax_id: string | null;
  address: string | null;
  phone: string | null;

  updated_at: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  color_hex: string;
  icon_name: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CategoryListResponse {
  items: Category[];
  total: number;
  source: string;
}

export interface Location {
  id: string;
  code: string;
  description: string | null;
  location_type: LocationType;
  capacity_units: number | null;
  is_active: boolean;
}

export interface LocationListResponse {
  items: Location[];
  total: number;
}

export type ItemType = "INGREDIENT" | "FINISHED_PRODUCT";

export interface SupplyItem {
  id: string;
  name: string;
  sku: string;
  description: string | null;
  item_type: ItemType;
  category_id: string;
  location_id: string;
  unit_of_measure: UnitMeasure;
  current_stock: string;
  minimum_stock: string;
  maximum_stock: string;
  unit_cost: string;
  is_perishable: boolean;
  expiration_date: string | null;
  supplier_name: string | null;
  is_active: boolean;
  is_below_minimum: boolean;
}

export interface SupplyItemListResponse {
  items: SupplyItem[];
  total: number;
  low_stock_count: number;
  page: number;
  limit: number;
}

// ── Lotes (HU-13 / HU-16) ────────────────────────────────────────────────────
export interface Batch {
  id: string;
  supply_item_id: string;
  batch_code: string;
  initial_stock: string;
  current_stock: string;
  unit_cost: string;
  vendor_name: string | null;
  expiration_date: string | null;
  is_active: boolean;
}

export interface BatchListResponse {
  items: Batch[];
  total: number;
  total_stock: string;
}

// ── Historial de movimientos (HU-07) ─────────────────────────────────────────
export interface MovementHistoryItem {
  movement_id: string;
  movement_type: MovementType;
  quantity: string;
  stock_before: string;
  stock_after: string;
  executed_by_user_id: string;
  user_email: string;
  is_adjustment: boolean;
  adjustment_reason: string | null;
  notes: string | null;
  alert_triggered: boolean;
  created_at: string;
}

export interface MovementHistoryListResponse {
  items: MovementHistoryItem[];
  total: number;
  page: number;
  limit: number;
}

// ── Dashboard (HU-08 / HU-16) ─────────────────────────────────────────────────
export interface TopWastedSupply {
  supply_id: string;
  supply_name: string;
  total_wasted: string;
}

export interface KpisResponse {
  total_critical_items: number;
  movements_last_24h: number;
  top_wasted_supplies: TopWastedSupply[];
  source: string;
}

export interface FinancialsResponse {
  total_active_value: string;
  total_waste_loss: string;
  active_batches_count: number;
  period_start: string | null;
}

// ── Recetas / Producción (HU-15) ──────────────────────────────────────────────
export interface RecipeItem {
  supply_item_id: string;
  quantity_per_unit: string;
}

export interface Recipe {
  id: string;
  name: string;
  description: string | null;
  yield_unit: UnitMeasure;
  produces_supply_item_id: string | null;
  shelf_life_days: number | null;
  is_active: boolean;
  items: RecipeItem[];
}

export interface RecipeListResponse {
  items: Recipe[];
  total: number;
}

export interface BatchPickPlan {
  batch_code: string;
  expiration_date: string | null;
  take: string;
}

export interface SimulatedIngredient {
  supply_id: string;
  supply_name: string;
  required: string;
  available: string;
  sufficient: boolean;
  deficit: string;
  unit: UnitMeasure;
  location_code: string | null;
  location_type: LocationType | null;
  batch_plan: BatchPickPlan[];
}

export interface ProductionSimulationResponse {
  recipe_id: string;
  recipe_name: string;
  quantity: number;
  feasible: boolean;
  ingredients: SimulatedIngredient[];
  missing: SimulatedIngredient[];
}

export interface PreparationBatch {
  batch_code: string;
  expiration_date: string | null;
  quantity: string;
}

export interface PreparationIngredient {
  supply_item_id: string;
  supply_name: string;
  unit: UnitMeasure;
  location_code: string | null;
  quantity_consumed: string;
  unit_cost: string;
  batches: PreparationBatch[];
}

export interface ProductionPreparation {
  production_id: string;
  recipe_name: string;
  product_name: string | null;
  quantity_produced: string;
  total_ingredient_cost: string;
  performed_by_email: string;
  created_at: string;
  ingredients: PreparationIngredient[];
}

export interface ProducedIngredient {
  supply_id: string;
  supply_name: string;
  consumed: string;
  movement_id: string;
}

export interface ProductionResponse {
  recipe_id: string;
  recipe_name: string;
  quantity_produced: number;
  ingredients: ProducedIngredient[];
  production_id: string | null;
  product_supply_item_id: string | null;
  product_name: string | null;
  product_new_stock: string | null;
  total_ingredient_cost: string;
}

// ── Historial de producción (HU-17) ──────────────────────────────────────────
export interface ProductionRun {
  production_id: string;
  recipe_id: string;
  recipe_name: string;
  product_supply_item_id: string | null;
  product_name: string | null;
  quantity_produced: string;
  total_ingredient_cost: string;
  performed_by_email: string;
  created_at: string;
}

export interface ProductionHistoryResponse {
  items: ProductionRun[];
  total: number;
  page: number;
  limit: number;
}

// ── Usuarios / Auditoría (HU-10) ──────────────────────────────────────────────
export interface UserListResponse {
  items: User[];
  total: number;
}

export interface AuditLogEntry {
  action_type: string;
  entity_id: string;
  summary: string;
  timestamp: string;
}

export interface UserAuditLogResponse {
  user_id: string;
  email: string;
  total: number;
  entries: AuditLogEntry[];
  page: number;
  limit: number;
}

// ── Conciliación (HU-11) ──────────────────────────────────────────────────────
export interface ReconciliationResponse {
  audit_id: string;
  supply_id: string;
  delta: string;
  stock_before: string;
  stock_after: string;
  alert_triggered: boolean;
}

export interface MovementResponse {
  id: string;
  supply_item_id: string;
  movement_type: MovementType;
  quantity: string;
  stock_before: string;
  stock_after: string;
  notes: string | null;
  alert_triggered: boolean;
  performed_by: string;
  created_at: string;
}
