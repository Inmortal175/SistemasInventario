import "server-only";

import { cache } from "react";

import { apiFetch } from "./api";
import type {
  BatchListResponse,
  CategoryListResponse,
  FinancialsResponse,
  KpisResponse,
  LocationListResponse,
  MovementHistoryListResponse,
  ProductionHistoryResponse,
  RecipeListResponse,
  SupplyItem,
  SystemSettings,
  SupplyItemListResponse,
  User,
  UserAuditLogResponse,
  UserListResponse,
} from "./types";

export function getCategories(): Promise<CategoryListResponse> {
  return apiFetch<CategoryListResponse>("/categories");
}

export function getLocations(): Promise<LocationListResponse> {
  return apiFetch<LocationListResponse>("/locations");
}

export function getSupplies(params?: {
  category_id?: string;
  location_id?: string;
  item_type?: "INGREDIENT" | "FINISHED_PRODUCT";
  page?: number;
  limit?: number;
}): Promise<SupplyItemListResponse> {
  const search = new URLSearchParams();
  if (params?.category_id) search.set("category_id", params.category_id);
  if (params?.location_id) search.set("location_id", params.location_id);
  if (params?.item_type) search.set("item_type", params.item_type);
  if (params?.page) search.set("page", String(params.page));
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  return apiFetch<SupplyItemListResponse>(`/supplies${qs ? `?${qs}` : ""}`);
}

export function getSupply(id: string): Promise<SupplyItem> {
  return apiFetch<SupplyItem>(`/supplies/${id}`);
}

export function getSupplyBatches(id: string): Promise<BatchListResponse> {
  return apiFetch<BatchListResponse>(`/supplies/${id}/batches`);
}

export function getSupplyMovements(
  id: string,
  page = 1,
  limit = 50,
): Promise<MovementHistoryListResponse> {
  return apiFetch<MovementHistoryListResponse>(
    `/supplies/${id}/movements?page=${page}&limit=${limit}`,
  );
}

export function getKpis(): Promise<KpisResponse> {
  return apiFetch<KpisResponse>("/dashboard/kpis");
}

export function getFinancials(startDate?: string): Promise<FinancialsResponse> {
  const qs = startDate ? `?start_date=${startDate}` : "";
  return apiFetch<FinancialsResponse>(`/dashboard/financials${qs}`);
}

export function getRecipes(): Promise<RecipeListResponse> {
  return apiFetch<RecipeListResponse>("/recipes");
}

export function getProductionHistory(
  page = 1,
  limit = 20,
): Promise<ProductionHistoryResponse> {
  return apiFetch<ProductionHistoryResponse>(
    `/production/history?page=${page}&limit=${limit}`,
  );
}

export function getMe(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

export function getUsers(): Promise<UserListResponse> {
  return apiFetch<UserListResponse>("/users");
}

export function getUserAuditLog(
  id: string,
  page = 1,
  limit = 20,
): Promise<UserAuditLogResponse> {
  return apiFetch<UserAuditLogResponse>(
    `/users/${id}/audit-log?page=${page}&limit=${limit}`,
  );
}

const FALLBACK_SETTINGS: SystemSettings = {
  app_name: "PastryStock Manager",
  logo_url: null,
  theme: "rosa",
  login_bg_mobile_url: null,
  login_bg_tablet_url: null,
  login_bg_desktop_url: null,
  login_overlay_opacity: 40,
  expiration_alert_days: 5,
  currency_code: "PEN",
  locale: "es-PE",
  page_size: 15,
  business_name: null,
  tax_id: null,
  address: null,
  phone: null,
  updated_at: "",
};

/** El layout raíz y el login dependen de esto en cada render, incluso sin sesión.
 *  Si el backend no responde, la app debe seguir pintándose con la marca por
 *  defecto en vez de mostrar una pantalla de error.
 *
 *  `cache()` deduplica la llamada dentro de un mismo request: generateMetadata
 *  y el layout la piden por separado. */
export const getSettings = cache(async (): Promise<SystemSettings> => {
  try {
    return await apiFetch<SystemSettings>("/settings", { auth: false });
  } catch {
    return FALLBACK_SETTINGS;
  }
});
