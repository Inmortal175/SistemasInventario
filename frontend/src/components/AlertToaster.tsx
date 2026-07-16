"use client";

import { useEffect, useState } from "react";

import { Icon } from "@/components/Icon";

interface Toast {
  id: number;
  kind: "low_stock" | "expiration_critical";
  title: string;
  detail: string;
}

function wsUrl(token: string): string {
  const api =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  const ws = api.replace(/^http/, "ws");
  return `${ws}/ws/notifications?token=${encodeURIComponent(token)}`;
}

export function AlertToaster({ token }: { token: string | null }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    if (!token) return;
    let socket: WebSocket | null = null;
    let closed = false;
    let counter = 0;

    function connect() {
      if (closed) return;
      socket = new WebSocket(wsUrl(token!));

      socket.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "low_stock") {
            const d = msg.data ?? {};
            pushToast({
              kind: "low_stock",
              title: `Stock crítico: ${d.supply_name ?? "insumo"}`,
              detail: `Actual ${d.current_stock} / mín ${d.minimum_stock} (déficit ${d.deficit})`,
            });
          } else if (msg.type === "expiration_critical") {
            const d = msg.data ?? {};
            pushToast({
              kind: "expiration_critical",
              title: `Lote por vencer: ${d.batch_code ?? ""}`,
              detail: `Vence ${d.expiration_date} · faltan ${d.days_left} día(s)`,
            });
          }
        } catch {
          // mensaje no-JSON (p. ej. bienvenida): se ignora
        }
      };

      // Reconexión simple si el socket cae y la sesión sigue viva.
      socket.onclose = () => {
        if (!closed) setTimeout(connect, 5000);
      };
    }

    function pushToast(t: Omit<Toast, "id">) {
      const id = ++counter;
      setToasts((prev) => [...prev, { ...t, id }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== id));
      }, 8000);
    }

    connect();
    return () => {
      closed = true;
      socket?.close();
    };
  }, [token]);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex w-80 flex-col gap-3">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className={`flex items-start gap-3 rounded-xl border p-4 shadow-lg ${
            t.kind === "low_stock"
              ? "border-red-200 bg-red-50"
              : "border-amber-200 bg-amber-50"
          }`}
        >
          <span
            className={
              t.kind === "low_stock" ? "text-red-500" : "text-amber-500"
            }
          >
            <Icon name="alert" />
          </span>
          <div className="text-sm">
            <p className="font-semibold text-slate-800">{t.title}</p>
            <p className="text-slate-500">{t.detail}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
