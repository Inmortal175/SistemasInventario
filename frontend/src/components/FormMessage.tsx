import type { FormState } from "@/lib/form";

export function FormMessage({ state }: { state: FormState }) {
  if (state.status === "idle" || !state.message) return null;

  const isError = state.status === "error";
  return (
    <p
      role={isError ? "alert" : "status"}
      className={`rounded-lg px-3 py-2 text-sm ${
        isError
          ? "bg-red-50 text-red-700"
          : "bg-emerald-50 text-emerald-700"
      }`}
    >
      {state.message}
    </p>
  );
}
