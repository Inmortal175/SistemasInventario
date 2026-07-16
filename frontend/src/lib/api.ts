import "server-only";

import { getToken } from "./session";

const DEFAULT_API_URL = "http://localhost:8000/api/v1";

// En el contenedor, el server component habla con el backend por la red interna
// de Docker (INTERNAL_API_URL); en local cae a NEXT_PUBLIC_API_URL.
function baseUrl(): string {
  return (
    process.env.INTERNAL_API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    DEFAULT_API_URL
  );
}

export class ApiError extends Error {
  status: number;
  code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** Adjunta el bearer de la sesión. Por defecto true. */
  auth?: boolean;
  /** Envía el body como x-www-form-urlencoded (login OAuth2). */
  form?: boolean;
  /** Revalidación de fetch de Next; por defecto sin caché. */
  cache?: RequestCache;
}

async function parseError(res: Response): Promise<ApiError> {
  let message = `Error ${res.status}`;
  let code: string | null = null;
  try {
    const data = await res.json();
    const detail = data?.detail ?? data;
    if (typeof detail === "string") {
      message = detail;
    } else if (detail && typeof detail === "object") {
      message = detail.message ?? message;
      code = detail.error_code ?? null;
    }
  } catch {
    // respuesta sin cuerpo JSON: se conserva el mensaje genérico
  }
  return new ApiError(res.status, message, code);
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, auth = true, form = false, cache = "no-store" } =
    options;

  const headers: Record<string, string> = {};
  if (auth) {
    const token = await getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let payload: BodyInit | undefined;
  if (body !== undefined) {
    if (form) {
      headers["Content-Type"] = "application/x-www-form-urlencoded";
      payload = new URLSearchParams(body as Record<string, string>).toString();
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }

  const res = await fetch(`${baseUrl()}${path}`, {
    method,
    headers,
    body: payload,
    cache,
  });

  if (!res.ok) {
    throw await parseError(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}
