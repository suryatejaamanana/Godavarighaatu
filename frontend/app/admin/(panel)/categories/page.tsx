"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/admin/confirm-dialog";
import { Field } from "@/components/admin/field";
import { PageHeader } from "@/components/admin/page-header";
import { EmptyState, ErrorState, LoadingRows } from "@/components/admin/query-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useCan } from "@/hooks/use-admin";
import { createCategory, deleteCategory, listCategories, updateCategory } from "@/services/admin";
import type { Category } from "@/types/api";

interface FormState {
  name: string;
  name_te: string;
  slug: string;
  description: string;
  description_te: string;
  sort_order: string;
  is_active: boolean;
}

const blank: FormState = { name: "", name_te: "", slug: "", description: "", description_te: "", sort_order: "0", is_active: true };
const toForm = (c: Category): FormState => ({
  name: c.name,
  name_te: c.name_te ?? "",
  slug: c.slug,
  description: c.description ?? "",
  description_te: c.description_te ?? "",
  sort_order: String(c.sort_order),
  is_active: c.is_active,
});

function CategoryDialog({ category, open, onClose }: { category: Category | null; open: boolean; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<FormState>(category ? toForm(category) : blank);
  const [error, setError] = useState<string | null>(null);
  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((f) => ({ ...f, [key]: value }));

  const save = useMutation({
    mutationFn: () => {
      const body = {
        name: form.name.trim(),
        name_te: form.name_te.trim() || null,
        description: form.description.trim() || null,
        description_te: form.description_te.trim() || null,
        sort_order: Number(form.sort_order) || 0,
        is_active: form.is_active,
      };
      if (category) return updateCategory(category.id, { ...body, slug: form.slug.trim() || undefined });
      return createCategory({ ...body, slug: form.slug.trim() || undefined });
    },
    onSuccess: () => {
      toast.success(category ? "Category updated" : "Category created");
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      onClose();
    },
    onError: (e: Error) => setError(e.message),
  });

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{category ? "Edit category" : "New category"}</DialogTitle>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            save.mutate();
          }}
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Name (English)" htmlFor="c-name">
              <Input id="c-name" required value={form.name} onChange={(e) => set("name", e.target.value)} />
            </Field>
            <Field label="Name (తెలుగు)" htmlFor="c-name-te">
              <Input id="c-name-te" value={form.name_te} onChange={(e) => set("name_te", e.target.value)} />
            </Field>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="URL slug" htmlFor="c-slug" hint="Lowercase letters, numbers, hyphens. Leave empty to generate from the name.">
              <Input id="c-slug" value={form.slug} onChange={(e) => set("slug", e.target.value)} />
            </Field>
            <Field label="Display order" htmlFor="c-order">
              <Input id="c-order" type="number" value={form.sort_order} onChange={(e) => set("sort_order", e.target.value)} />
            </Field>
          </div>
          <Field label="Description" htmlFor="c-desc">
            <Textarea id="c-desc" rows={2} value={form.description} onChange={(e) => set("description", e.target.value)} />
          </Field>
          <Field label="వివరణ (Telugu description)" htmlFor="c-desc-te">
            <Textarea id="c-desc-te" rows={2} value={form.description_te} onChange={(e) => set("description_te", e.target.value)} />
          </Field>
          <label className="flex items-center gap-3 text-sm">
            <Switch checked={form.is_active} onCheckedChange={(v) => set("is_active", v)} aria-label="Active" />
            Active (visible in the shop)
          </label>
          {error && (
            <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={save.isPending || !form.name.trim()}>
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export default function CategoriesPage() {
  const canEdit = useCan("manager");
  const queryClient = useQueryClient();
  const categories = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const [editing, setEditing] = useState<Category | null | "new">(null);
  const [deleting, setDeleting] = useState<Category | null>(null);

  const remove = useMutation({
    mutationFn: (id: string) => deleteCategory(id),
    onSuccess: () => {
      toast.success("Category deleted");
      queryClient.invalidateQueries({ queryKey: ["categories"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <>
      <PageHeader
        title="Categories"
        description="Group your pickles. Inactive categories are hidden from the shop."
        actions={
          canEdit && (
            <Button onClick={() => setEditing("new")}>
              <Plus /> New category
            </Button>
          )
        }
      />

      {categories.isPending ? (
        <LoadingRows />
      ) : categories.isError ? (
        <ErrorState error={categories.error} onRetry={() => categories.refetch()} />
      ) : categories.data.length === 0 ? (
        <EmptyState
          title="No categories yet"
          hint="Create categories such as Veg Pickles or Non-Veg Pickles."
          action={canEdit && <Button onClick={() => setEditing("new")}>Create the first category</Button>}
        />
      ) : (
        <ul className="divide-y rounded-lg border bg-card">
          {categories.data.map((c) => (
            <li key={c.id} className="flex flex-wrap items-center gap-3 p-3 sm:p-4">
              <div className="min-w-0 flex-1">
                <div className="font-medium">
                  {c.name} {c.name_te && <span className="text-muted-foreground">· {c.name_te}</span>}
                </div>
                <div className="text-xs text-muted-foreground">/{c.slug} · order {c.sort_order}</div>
              </div>
              <Badge variant={c.is_active ? "default" : "secondary"}>{c.is_active ? "Active" : "Hidden"}</Badge>
              {canEdit && (
                <div className="flex gap-1">
                  <Button variant="outline" size="icon" aria-label={`Edit ${c.name}`} onClick={() => setEditing(c)}>
                    <Pencil />
                  </Button>
                  <Button variant="destructive" size="icon" aria-label={`Delete ${c.name}`} onClick={() => setDeleting(c)}>
                    <Trash2 />
                  </Button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {editing !== null && (
        <CategoryDialog
          key={editing === "new" ? "new" : editing.id}
          category={editing === "new" ? null : editing}
          open
          onClose={() => setEditing(null)}
        />
      )}
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => !o && setDeleting(null)}
        title={`Delete “${deleting?.name}”?`}
        description="This cannot be undone. A category that still has products cannot be deleted; hide it instead."
        onConfirm={() => deleting && remove.mutate(deleting.id)}
      />
    </>
  );
}
