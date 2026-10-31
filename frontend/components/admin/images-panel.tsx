"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, ImagePlus, Star, Trash2 } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/admin/confirm-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCan } from "@/hooks/use-admin";
import { deleteImage, reorderImages, updateImage, uploadImage } from "@/services/admin";
import type { Product, ProductImage } from "@/types/api";

const MAX_MB = 10;
const MAX_IMAGES = 10;
const ACCEPT = "image/jpeg,image/png,image/webp";

export function ImagesPanel({ product }: { product: Product }) {
  const canEdit = useCan("manager");
  const queryClient = useQueryClient();
  const input = useRef<HTMLInputElement>(null);
  const [deleting, setDeleting] = useState<ProductImage | null>(null);
  const [dragging, setDragging] = useState(false);
  const images = [...product.images].sort((a, b) => a.sort_order - b.sort_order);

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["product", product.id] });
    queryClient.invalidateQueries({ queryKey: ["products"] });
  };
  const fail = (e: Error) => toast.error(e.message);

  const upload = useMutation({
    mutationFn: async (files: File[]) => {
      // sequential: keeps the upload order and the first image becomes the primary one
      for (const file of files) await uploadImage(product.id, file, product.name);
    },
    onSuccess: () => toast.success("Image uploaded"),
    onError: fail,
    onSettled: refresh,
  });
  const makePrimary = useMutation({ mutationFn: (id: string) => updateImage(id, { is_primary: true }), onSuccess: refresh, onError: fail });
  const reorder = useMutation({ mutationFn: (ids: string[]) => reorderImages(product.id, ids), onSuccess: refresh, onError: fail });
  const remove = useMutation({
    mutationFn: (id: string) => deleteImage(id),
    onSuccess: () => {
      toast.success("Image deleted");
      refresh();
    },
    onError: fail,
  });

  function pick(list: FileList | null) {
    const files = Array.from(list ?? []);
    if (input.current) input.current.value = "";
    if (files.length === 0) return;
    if (images.length + files.length > MAX_IMAGES) return void toast.error(`A product can have up to ${MAX_IMAGES} images.`);
    const bad = files.find((f) => !ACCEPT.split(",").includes(f.type));
    if (bad) return void toast.error(`${bad.name}: only JPEG, PNG or WebP images are allowed.`);
    const big = files.find((f) => f.size > MAX_MB * 1024 * 1024);
    if (big) return void toast.error(`${big.name} is larger than ${MAX_MB} MB.`);
    upload.mutate(files);
  }

  function move(index: number, delta: number) {
    const ids = images.map((i) => i.id);
    [ids[index], ids[index + delta]] = [ids[index + delta], ids[index]];
    reorder.mutate(ids);
  }

  return (
    <div className="space-y-4">
      {canEdit && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            pick(e.dataTransfer.files);
          }}
          className={`rounded-lg border-2 border-dashed p-6 text-center transition-colors ${dragging ? "border-brand-red bg-brand-red/5" : ""}`}
        >
          <ImagePlus className="mx-auto mb-2 size-8 text-muted-foreground" />
          <p className="text-sm">Drag photos here, or</p>
          <Button className="mt-2" disabled={upload.isPending || images.length >= MAX_IMAGES} onClick={() => input.current?.click()}>
            {upload.isPending ? "Uploading…" : "Choose photos"}
          </Button>
          <input ref={input} type="file" accept={ACCEPT} multiple hidden aria-label="Upload product photos" onChange={(e) => pick(e.target.files)} />
          <p className="mt-2 text-xs text-muted-foreground">
            JPEG, PNG or WebP, up to {MAX_MB} MB each, {MAX_IMAGES} per product. Full HD (1920px) photos are kept sharp; smaller sizes are made automatically.
          </p>
        </div>
      )}

      {images.length === 0 ? (
        <p className="text-center text-sm text-muted-foreground">No photos yet. Until you add one, the shop shows a placeholder.</p>
      ) : (
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
          {images.map((img, i) => (
            <li key={img.id} className="overflow-hidden rounded-lg border bg-card">
              <div className="relative aspect-square bg-muted">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={img.card_url} alt={img.alt_text ?? product.name} className="size-full object-cover" loading="lazy" />
                {img.is_primary && <Badge className="absolute left-2 top-2">Main photo</Badge>}
              </div>
              {canEdit && (
                <div className="flex items-center justify-between gap-1 p-2">
                  <div className="flex gap-1">
                    <Button variant="outline" size="icon" disabled={i === 0 || reorder.isPending} aria-label={`Move photo ${i + 1} earlier`} onClick={() => move(i, -1)}>
                      <ArrowLeft />
                    </Button>
                    <Button variant="outline" size="icon" disabled={i === images.length - 1 || reorder.isPending} aria-label={`Move photo ${i + 1} later`} onClick={() => move(i, 1)}>
                      <ArrowRight />
                    </Button>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="outline" size="icon" disabled={img.is_primary || makePrimary.isPending} aria-label={`Make photo ${i + 1} the main photo`} onClick={() => makePrimary.mutate(img.id)}>
                      <Star />
                    </Button>
                    <Button variant="destructive" size="icon" aria-label={`Delete photo ${i + 1}`} onClick={() => setDeleting(img)}>
                      <Trash2 />
                    </Button>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title="Delete this photo?"
        description="The photo is removed from storage and the shop. This cannot be undone."
        onConfirm={() => deleting && remove.mutate(deleting.id)}
      />
    </div>
  );
}
