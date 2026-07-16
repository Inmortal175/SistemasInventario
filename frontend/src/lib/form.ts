// Estado compartido de formularios para usar con React `useActionState`.

export interface FormState {
  status: "idle" | "success" | "error";
  message?: string;
}

export const IDLE: FormState = { status: "idle" };

export function ok(message?: string): FormState {
  return { status: "success", message };
}

export function fail(message: string): FormState {
  return { status: "error", message };
}
