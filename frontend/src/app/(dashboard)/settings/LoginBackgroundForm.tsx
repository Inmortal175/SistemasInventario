"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, useTransition } from "react";

import { removeLoginBackgroundAction } from "@/app/actions/settings";
import { Icon } from "@/components/Icon";
import { ImageCropper, type CropOutput } from "@/components/ImageCropper";
import { assetUrl } from "@/lib/labels";
import type { LoginBackgroundDevice, SystemSettings } from "@/lib/types";

interface Slot {
  device: LoginBackgroundDevice;
  label: string;
  hint: string;
  output: CropOutput;
  /** Proporción de la miniatura, para que se vea como el dispositivo real. */
  thumb: string;
}

// Deben coincidir con LOGIN_BACKGROUND_SIZES del backend.
const SLOTS: Slot[] = [
  {
    device: "mobile",
    label: "Móvil",
    hint: "menos de 768 px · 9:16",
    output: { width: 720, height: 1280, type: "image/jpeg", quality: 0.85 },
    thumb: "9 / 16",
  },
  {
    device: "tablet",
    label: "Tablet",
    hint: "768–1023 px · 3:4",
    output: { width: 900, height: 1200, type: "image/jpeg", quality: 0.85 },
    thumb: "3 / 4",
  },
  {
    device: "desktop",
    label: "Escritorio",
    hint: "1024 px o más · 16:9",
    output: { width: 1920, height: 1080, type: "image/jpeg", quality: 0.85 },
    thumb: "16 / 9",
  },
];

const FIELD: Record<LoginBackgroundDevice, keyof SystemSettings> = {
  mobile: "login_bg_mobile_url",
  tablet: "login_bg_tablet_url",
  desktop: "login_bg_desktop_url",
};

export function LoginBackgroundForm({ settings }: { settings: SystemSettings }) {
  const router = useRouter();
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({});
  const [active, setActive] = useState<Slot | null>(null);
  const [source, setSource] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const busy = uploading || pending;

  function closeCropper() {
    if (active) {
      const input = inputRefs.current[active.device];
      // Sin esto, volver a elegir el mismo archivo no dispara `change`.
      if (input) input.value = "";
    }
    setSource(null);
    setActive(null);
  }

  async function upload(cropped: File) {
    if (!active) return;
    setUploading(true);
    setError(null);

    const form = new FormData();
    form.append("file", cropped);

    try {
      const res = await fetch(`/api/settings/login-background/${active.device}`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data?.detail ?? "No se pudo subir la imagen.");
        return;
      }
      closeCropper();
      startTransition(() => router.refresh());
    } finally {
      setUploading(false);
    }
  }

  function remove(device: LoginBackgroundDevice) {
    setError(null);
    startTransition(async () => {
      await removeLoginBackgroundAction(device);
      router.refresh();
    });
  }

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-3">
        {SLOTS.map((slot) => {
          const url = assetUrl(settings[FIELD[slot.device]] as string | null);
          return (
            <div key={slot.device} className="flex flex-col">
              <div
                style={{ aspectRatio: slot.thumb }}
                className="mb-2 flex w-full items-center justify-center overflow-hidden rounded-xl border border-brand-100 bg-brand-50 text-brand-300"
              >
                {url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={url}
                    alt={`Fondo de ${slot.label}`}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <Icon name="image" />
                )}
              </div>

              <p className="text-sm font-medium text-slate-700">{slot.label}</p>
              <p className="mb-2 text-xs text-slate-400">{slot.hint}</p>

              <input
                ref={(el) => {
                  inputRefs.current[slot.device] = el;
                }}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  setError(null);
                  setActive(slot);
                  setSource(f);
                }}
              />

              <div className="mt-auto flex flex-wrap gap-2">
                <button
                  type="button"
                  className="btn-ghost text-xs"
                  disabled={busy}
                  onClick={() => inputRefs.current[slot.device]?.click()}
                >
                  <Icon name="add" /> {url ? "Cambiar" : "Subir"}
                </button>
                {url && (
                  <button
                    type="button"
                    className="btn-ghost text-xs"
                    disabled={busy}
                    onClick={() => remove(slot.device)}
                  >
                    <Icon name="close" /> Quitar
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <p className="mt-3 text-xs text-slate-400">
        Puedes subir solo una: si falta la de móvil se usa la de tablet, y si falta la
        de tablet se usa la de escritorio. Sin ninguna, el login queda con el fondo liso.
      </p>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}

      {source && active && (
        <ImageCropper
          file={source}
          output={active.output}
          title={`Recorta el fondo de ${active.label.toLowerCase()}`}
          pending={uploading}
          onCancel={closeCropper}
          onConfirm={upload}
        />
      )}
    </>
  );
}
