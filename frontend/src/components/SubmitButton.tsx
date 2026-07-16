"use client";

import { useFormStatus } from "react-dom";

interface Props {
  children: React.ReactNode;
  pendingText?: string;
  className?: string;
}

export function SubmitButton({ children, pendingText, className }: Props) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className={className ?? "btn-primary"}
    >
      {pending ? pendingText ?? "Guardando…" : children}
    </button>
  );
}
