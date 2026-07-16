"use client";

import { useRouter } from "next/navigation";
import { useRef, useState, useTransition } from "react";

import { Icon } from "@/components/Icon";
import { ImageCropper } from "@/components/ImageCropper";
import { assetUrl } from "@/lib/labels";

export function AvatarForm({ currentAvatar }: { currentAvatar: string | null }) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(assetUrl(currentAvatar));
  const [source, setSource] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [pending, startTransition] = useTransition();

  function closeCropper() {
    setSource(null);
    // Sin esto, volver a elegir el mismo archivo no dispara `change`.
    if (inputRef.current) inputRef.current.value = "";
  }

  async function upload(cropped: File) {
    setUploading(true);
    setError(null);
    const previous = preview;
    setPreview(URL.createObjectURL(cropped));

    const form = new FormData();
    form.append("file", cropped);

    try {
      const res = await fetch("/api/profile/avatar", { method: "POST", body: form });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data?.detail ?? "No se pudo subir la imagen.");
        setPreview(previous);
        return;
      }
      const data = await res.json();
      setPreview(assetUrl(data.avatar_url));
      closeCropper();
      // Refresca los server components (menú y perfil) para reflejar el avatar.
      startTransition(() => router.refresh());
    } finally {
      setUploading(false);
    }
  }

  const busy = uploading || pending;

  return (
    <>
      <div className="flex items-center gap-4">
        <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full border border-brand-100 bg-brand-50 text-2xl text-brand-300">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Avatar" className="h-full w-full object-cover" />
          ) : (
            <Icon name="users" />
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
              if (f) {
                setError(null);
                setSource(f);
              }
            }}
          />
          <button
            type="button"
            className="btn-ghost"
            disabled={busy}
            onClick={() => inputRef.current?.click()}
          >
            <Icon name="add" /> {busy ? "Subiendo…" : "Cambiar foto"}
          </button>
          <p className="mt-1 text-xs text-slate-400">
            JPG, PNG o WebP · máx 2 MB. Elegirás el recorte cuadrado antes de subir.
          </p>
          {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
        </div>
      </div>

      {source && (
        <ImageCropper
          file={source}
          output={{ width: 256, height: 256, type: "image/png" }}
          title="Recorta tu foto (1:1)"
          pending={uploading}
          onCancel={closeCropper}
          onConfirm={upload}
        />
      )}
    </>
  );
}
