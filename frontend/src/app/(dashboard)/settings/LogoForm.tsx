"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, useTransition } from "react";

import { removeLogoAction } from "@/app/actions/settings";
import { Icon } from "@/components/Icon";
import { ImageCropper } from "@/components/ImageCropper";
import { assetUrl } from "@/lib/labels";

export function LogoForm({ currentLogo }: { currentLogo: string | null }) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(assetUrl(currentLogo));
  const [source, setSource] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [pending, startTransition] = useTransition();

  function pickFile(file: File) {
    setError(null);
    setSource(file);
  }

  function closeCropper() {
    setSource(null);
    // Sin esto, volver a elegir el mismo archivo no dispara `change`.
    if (inputRef.current) inputRef.current.value = "";
  }

  async function uploadCropped(cropped: File) {
    setUploading(true);
    const previous = preview;
    setPreview(URL.createObjectURL(cropped));

    const form = new FormData();
    form.append("file", cropped);

    try {
      const res = await fetch("/api/settings/logo", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data?.detail ?? "No se pudo subir la imagen.");
        setPreview(previous);
        return;
      }
      const data = await res.json();
      setPreview(assetUrl(data.logo_url));
      closeCropper();
      startTransition(() => router.refresh());
    } finally {
      setUploading(false);
    }
  }

  function handleRemove() {
    setError(null);
    startTransition(async () => {
      await removeLogoAction();
      setPreview(null);
      router.refresh();
    });
  }

  const busy = pending || uploading;

  return (
    <>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-2xl border border-brand-100 bg-brand-50 text-3xl text-brand-300">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Logo" className="h-full w-full object-contain" />
          ) : (
            <span aria-hidden>🧁</span>
          )}
        </div>

        <div>
          <input
            ref={inputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) pickFile(f);
            }}
          />
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-ghost"
              disabled={busy}
              onClick={() => inputRef.current?.click()}
            >
              <Icon name="add" /> {busy ? "Guardando…" : "Subir logo"}
            </button>
            {preview && (
              <button
                type="button"
                className="btn-ghost"
                disabled={busy}
                onClick={handleRemove}
              >
                <Icon name="close" /> Quitar
              </button>
            )}
          </div>
          <p className="mt-1 text-xs text-slate-400">
            JPG, PNG o WebP · máx 2 MB. Elegirás el recorte cuadrado (1:1) antes de subir.
          </p>
          {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
        </div>
      </div>

      {source && (
        <ImageCropper
          file={source}
          output={{ width: 512, height: 512, type: "image/png" }}
          title="Recorta el logo (1:1)"
          pending={uploading}
          onCancel={closeCropper}
          onConfirm={uploadCropped}
        />
      )}
    </>
  );
}
