"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Icon } from "@/components/Icon";

const MAX_ZOOM = 4;

export interface CropOutput {
  width: number;
  height: number;
  /** "image/png" conserva transparencia (logo); "image/jpeg" pesa mucho menos
   *  en fotos a pantalla completa (fondos). */
  type: "image/png" | "image/jpeg";
  /** Solo aplica a JPEG. */
  quality?: number;
}

interface Props {
  file: File;
  /** Proporción del recuadro, ancho/alto. 1 = cuadrado, 16/9 = panorámico. */
  output: CropOutput;
  title: string;
  onCancel: () => void;
  onConfirm: (cropped: File) => void;
  pending?: boolean;
}

interface Transform {
  /** Posición del borde superior izquierdo de la imagen, en px del recuadro. */
  tx: number;
  ty: number;
  /** Escala aplicada sobre las dimensiones naturales. */
  scale: number;
}

export function ImageCropper({
  file,
  output,
  title,
  onCancel,
  onConfirm,
  pending = false,
}: Props) {
  const viewportRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const dragRef = useRef<{ x: number; y: number; tx: number; ty: number } | null>(null);

  const [src, setSrc] = useState<string | null>(null);
  const [box, setBox] = useState({ w: 0, h: 0 });
  const [natural, setNatural] = useState<{ w: number; h: number } | null>(null);
  const [zoom, setZoom] = useState(1);
  const [t, setT] = useState<Transform>({ tx: 0, ty: 0, scale: 0 });

  const aspect = output.width / output.height;

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setSrc(url);
    setNatural(null);
    setZoom(1);
    setT({ tx: 0, ty: 0, scale: 0 });
    return () => URL.revokeObjectURL(url);
  }, [file]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onCancel]);

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const measure = () =>
      setBox({ w: el.clientWidth, h: el.clientHeight });
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [src]);

  /** Escala mínima con la que la imagen sigue cubriendo el recuadro completo. */
  const baseScale = useCallback(() => {
    if (!natural || !box.w || !box.h) return 1;
    return Math.max(box.w / natural.w, box.h / natural.h);
  }, [natural, box]);

  /** Impide que aparezcan franjas vacías dentro del recuadro. */
  const clamp = useCallback(
    (tx: number, ty: number, scale: number): Transform => {
      if (!natural) return { tx, ty, scale };
      return {
        scale,
        tx: Math.min(0, Math.max(box.w - natural.w * scale, tx)),
        ty: Math.min(0, Math.max(box.h - natural.h * scale, ty)),
      };
    },
    [natural, box],
  );

  function handleLoad(e: React.SyntheticEvent<HTMLImageElement>) {
    const img = e.currentTarget;
    imageRef.current = img;
    setNatural({ w: img.naturalWidth, h: img.naturalHeight });
  }

  // El encuadre inicial necesita el tamaño natural Y el del recuadro, y no hay
  // garantía de cuál llega primero: `onLoad` y el ResizeObserver corren sueltos.
  useEffect(() => {
    if (!natural || !box.w || !box.h) return;
    setT((prev) => {
      if (prev.scale > 0) return prev;
      const s = Math.max(box.w / natural.w, box.h / natural.h);
      return {
        scale: s,
        tx: (box.w - natural.w * s) / 2,
        ty: (box.h - natural.h * s) / 2,
      };
    });
  }, [natural, box]);

  function handleZoom(nextZoom: number) {
    if (!natural) return;
    const scale = baseScale() * nextZoom;
    // Mantiene fijo el punto central del recuadro al acercar o alejar.
    const cx = (box.w / 2 - t.tx) / t.scale;
    const cy = (box.h / 2 - t.ty) / t.scale;
    setZoom(nextZoom);
    setT(clamp(box.w / 2 - cx * scale, box.h / 2 - cy * scale, scale));
  }

  function onPointerDown(e: React.PointerEvent<HTMLDivElement>) {
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = { x: e.clientX, y: e.clientY, tx: t.tx, ty: t.ty };
  }

  function onPointerMove(e: React.PointerEvent<HTMLDivElement>) {
    const d = dragRef.current;
    if (!d) return;
    setT(clamp(d.tx + (e.clientX - d.x), d.ty + (e.clientY - d.y), t.scale));
  }

  function onPointerUp(e: React.PointerEvent<HTMLDivElement>) {
    e.currentTarget.releasePointerCapture(e.pointerId);
    dragRef.current = null;
  }

  async function confirm() {
    const img = imageRef.current;
    if (!img || !natural || t.scale <= 0) return;

    // El recuadro visible, traducido a coordenadas de la imagen original.
    const sx = -t.tx / t.scale;
    const sy = -t.ty / t.scale;
    const sw = box.w / t.scale;
    const sh = box.h / t.scale;

    const canvas = document.createElement("canvas");
    canvas.width = output.width;
    canvas.height = output.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.imageSmoothingQuality = "high";
    if (output.type === "image/jpeg") {
      // JPEG no tiene alfa: sin esto, una PNG transparente sale con fondo negro.
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, output.width, output.height);
    }
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, output.width, output.height);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, output.type, output.quality),
    );
    if (!blob) return;

    const ext = output.type === "image/jpeg" ? "jpg" : "png";
    onConfirm(new File([blob], `crop.${ext}`, { type: output.type }));
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <button
        type="button"
        aria-label="Cancelar recorte"
        onClick={onCancel}
        className="absolute inset-0 h-full w-full bg-slate-900/50"
      />

      <div className="relative flex max-h-[92vh] w-full max-w-md flex-col overflow-y-auto rounded-t-2xl bg-white shadow-xl sm:rounded-2xl">
        <div className="flex items-center justify-between border-b border-brand-100 px-5 py-4">
          <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Cancelar recorte"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 hover:bg-brand-100"
          >
            <Icon name="close" />
          </button>
        </div>

        <div className="px-5 py-4">
          {/* `aspect-ratio` exige que solo una dimensión esté fijada: en
              apaisado manda el ancho; en vertical, el alto, o un recuadro 9:16
              desbordaría la pantalla. */}
          <div
            ref={viewportRef}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            style={
              aspect >= 1
                ? { aspectRatio: String(aspect), width: "100%" }
                : { aspectRatio: String(aspect), height: "46vh" }
            }
            className="relative mx-auto cursor-grab touch-none overflow-hidden rounded-xl border border-brand-100 bg-brand-50 active:cursor-grabbing"
          >
            {src && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={src}
                alt=""
                draggable={false}
                onLoad={handleLoad}
                style={{
                  position: "absolute",
                  transformOrigin: "top left",
                  transform: `translate(${t.tx}px, ${t.ty}px) scale(${t.scale})`,
                  width: natural ? `${natural.w}px` : "auto",
                  maxWidth: "none",
                }}
              />
            )}
          </div>

          <label className="mt-4 block">
            <span className="label">Zoom</span>
            <input
              type="range"
              min={1}
              max={MAX_ZOOM}
              step={0.01}
              value={zoom}
              onChange={(e) => handleZoom(Number(e.target.value))}
              className="w-full accent-brand-500"
            />
          </label>

          <p className="text-xs text-slate-400">
            Arrastra para encuadrar. El área visible es exactamente lo que se guarda
            ({output.width}×{output.height}).
          </p>
        </div>

        <div className="flex justify-end gap-2 border-t border-brand-100 px-5 py-4">
          <button type="button" className="btn-ghost" onClick={onCancel} disabled={pending}>
            Cancelar
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={confirm}
            disabled={pending || t.scale <= 0}
          >
            {pending ? "Subiendo…" : "Recortar y subir"}
          </button>
        </div>
      </div>
    </div>
  );
}
