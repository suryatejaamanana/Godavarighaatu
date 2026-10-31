"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Controller, useFieldArray, useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Field } from "@/components/admin/field";
import { ErrorState, LoadingRows } from "@/components/admin/query-state";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api";
import { createProduct, listCategories, updateProduct, type NewVariant } from "@/services/admin";
import { WEIGHTS, type Product, type Weight } from "@/types/api";

const money = z
  .string()
  .trim()
  .regex(/^\d{1,8}(\.\d{1,2})?$/, "Enter an amount like 350 or 350.50");

const schema = z.object({
  name: z.string().trim().min(1, "Name is required").max(200),
  name_te: z.string().max(200),
  slug: z.string().trim().regex(/^$|^[a-z0-9]+(?:-[a-z0-9]+)*$/, "Lowercase letters, numbers and hyphens only"),
  category_id: z.string().min(1, "Choose a category"),
  status: z.enum(["active", "inactive", "archived"]),
  short_description: z.string().max(300),
  short_description_te: z.string().max(300),
  description: z.string(),
  description_te: z.string(),
  ingredients: z.string(),
  ingredients_te: z.string(),
  preparation: z.string(),
  preparation_te: z.string(),
  storage_instructions: z.string(),
  storage_instructions_te: z.string(),
  shelf_life: z.string().max(100),
  badges: z.string(),
  is_featured: z.boolean(),
  is_best_seller: z.boolean(),
  is_new_arrival: z.boolean(),
  seo_title: z.string().max(200),
  seo_description: z.string().max(320),
  // only used when creating: quick-add variants
  variants: z.array(
    z.object({
      weight: z.enum(["250g", "500g", "1kg"]),
      enabled: z.boolean(),
      price: z.string(),
      quantity: z.string(),
    }),
  ),
}).superRefine((data, ctx) => {
  data.variants.forEach((v, i) => {
    if (!v.enabled) return;
    if (!money.safeParse(v.price).success) ctx.addIssue({ code: "custom", path: ["variants", i, "price"], message: "Enter a valid price" });
    if (!/^\d+$/.test(v.quantity.trim())) ctx.addIssue({ code: "custom", path: ["variants", i, "quantity"], message: "Whole number" });
  });
});

type FormValues = z.infer<typeof schema>;

const blankVariants = WEIGHTS.map((weight) => ({ weight, enabled: false, price: "", quantity: "0" }));

function toValues(p?: Product): FormValues {
  return {
    name: p?.name ?? "",
    name_te: p?.name_te ?? "",
    slug: p?.slug ?? "",
    category_id: p?.category_id ?? "",
    status: p?.status ?? "active",
    short_description: p?.short_description ?? "",
    short_description_te: p?.short_description_te ?? "",
    description: p?.description ?? "",
    description_te: p?.description_te ?? "",
    ingredients: p?.ingredients ?? "",
    ingredients_te: p?.ingredients_te ?? "",
    preparation: p?.preparation ?? "",
    preparation_te: p?.preparation_te ?? "",
    storage_instructions: p?.storage_instructions ?? "",
    storage_instructions_te: p?.storage_instructions_te ?? "",
    shelf_life: p?.shelf_life ?? "",
    badges: (p?.badges ?? []).join(", "),
    is_featured: p?.is_featured ?? false,
    is_best_seller: p?.is_best_seller ?? false,
    is_new_arrival: p?.is_new_arrival ?? false,
    seo_title: p?.seo_title ?? "",
    seo_description: p?.seo_description ?? "",
    variants: blankVariants,
  };
}

const nullable = (s: string) => (s.trim() === "" ? null : s.trim());

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4 rounded-lg border bg-card p-4 sm:p-5">
      <h2 className="font-semibold">{title}</h2>
      {children}
    </section>
  );
}

export function ProductForm({ product }: { product?: Product }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const categories = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const [formError, setFormError] = useState<string | null>(null);

  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: toValues(product) });
  const { register, control, handleSubmit, formState: { errors } } = form;
  const { fields } = useFieldArray({ control, name: "variants" });

  const save = useMutation({
    mutationFn: async (v: FormValues) => {
      const body = {
        name: v.name.trim(),
        name_te: nullable(v.name_te),
        category_id: v.category_id,
        status: v.status,
        short_description: nullable(v.short_description),
        short_description_te: nullable(v.short_description_te),
        description: nullable(v.description),
        description_te: nullable(v.description_te),
        ingredients: nullable(v.ingredients),
        ingredients_te: nullable(v.ingredients_te),
        preparation: nullable(v.preparation),
        preparation_te: nullable(v.preparation_te),
        storage_instructions: nullable(v.storage_instructions),
        storage_instructions_te: nullable(v.storage_instructions_te),
        shelf_life: nullable(v.shelf_life),
        badges: v.badges.split(",").map((b) => b.trim()).filter(Boolean),
        is_featured: v.is_featured,
        is_best_seller: v.is_best_seller,
        is_new_arrival: v.is_new_arrival,
        seo_title: nullable(v.seo_title),
        seo_description: nullable(v.seo_description),
      };
      if (product) return updateProduct(product.id, { ...body, slug: v.slug.trim() || undefined });
      const variants: NewVariant[] = v.variants
        .filter((x) => x.enabled)
        .map((x) => ({ weight: x.weight as Weight, price: x.price.trim(), quantity: Number(x.quantity) }));
      return createProduct({ ...body, slug: v.slug.trim() || undefined, variants });
    },
    onSuccess: (saved) => {
      toast.success(product ? "Product saved" : "Product created");
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["product", saved.id] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
      if (!product) router.replace(`/admin/products/${saved.id}`);
    },
    onError: (e: Error) => setFormError(e instanceof ApiError ? e.message : "Could not save the product."),
  });

  // The category <select> needs its options before it can show the saved value.
  if (categories.isPending) return <LoadingRows rows={4} />;
  if (categories.isError) return <ErrorState error={categories.error} onRetry={() => categories.refetch()} />;

  const text = (name: keyof FormValues & string, label: string, opts: { rows?: number; hint?: string } = {}) => (
    <Field label={label} htmlFor={`p-${name}`} error={(errors as Record<string, { message?: string }>)[name]?.message} hint={opts.hint}>
      {opts.rows ? <Textarea id={`p-${name}`} rows={opts.rows} {...register(name)} /> : <Input id={`p-${name}`} {...register(name)} />}
    </Field>
  );

  return (
    <form
      className="space-y-5"
      noValidate
      onSubmit={handleSubmit((v) => {
        setFormError(null);
        save.mutate(v);
      })}
    >
      <Section title="Basics">
        <div className="grid gap-4 sm:grid-cols-2">
          {text("name", "Name (English)")}
          {text("name_te", "Name (తెలుగు)")}
          <Field label="Category" htmlFor="p-category_id" error={errors.category_id?.message}>
            <NativeSelect id="p-category_id" aria-invalid={!!errors.category_id} {...register("category_id")}>
              <option value="">Choose…</option>
              {categories.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </NativeSelect>
          </Field>
          <Field label="Status" htmlFor="p-status" hint="Only Active products are shown in the shop.">
            <NativeSelect id="p-status" {...register("status")}>
              <option value="active">Active</option>
              <option value="inactive">Hidden</option>
              <option value="archived">Archived</option>
            </NativeSelect>
          </Field>
          {text("slug", "URL slug", { hint: product ? undefined : "Leave empty to generate from the English name." })}
          {text("shelf_life", "Shelf life", { hint: "For example: 6 months" })}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {text("badges", "Badges", { hint: "Comma separated, e.g. Bestseller, Homemade" })}
          <div className="flex flex-wrap items-end gap-x-6 gap-y-3 pb-1">
            {(
              [
                ["is_featured", "Featured"],
                ["is_best_seller", "Best seller"],
                ["is_new_arrival", "New arrival"],
              ] as const
            ).map(([name, label]) => (
              <Controller
                key={name}
                control={control}
                name={name}
                render={({ field }) => (
                  <label className="flex items-center gap-2 text-sm">
                    <Checkbox checked={field.value} onCheckedChange={(c) => field.onChange(c === true)} aria-label={label} />
                    {label}
                  </label>
                )}
              />
            ))}
          </div>
        </div>
      </Section>

      <Section title="Descriptions">
        <div className="grid gap-4 sm:grid-cols-2">
          {text("short_description", "Short description", { rows: 2 })}
          {text("short_description_te", "చిన్న వివరణ (Telugu)", { rows: 2 })}
          {text("description", "Full description", { rows: 4 })}
          {text("description_te", "పూర్తి వివరణ (Telugu)", { rows: 4 })}
          {text("ingredients", "Ingredients", { rows: 3 })}
          {text("ingredients_te", "కావలసిన పదార్థాలు (Telugu)", { rows: 3 })}
          {text("preparation", "Preparation details", { rows: 3 })}
          {text("preparation_te", "తయారీ విధానం (Telugu)", { rows: 3 })}
          {text("storage_instructions", "Storage instructions", { rows: 3 })}
          {text("storage_instructions_te", "నిల్వ సూచనలు (Telugu)", { rows: 3 })}
        </div>
      </Section>

      {!product && (
        <Section title="Sizes, prices and stock">
          <p className="-mt-2 text-sm text-muted-foreground">Tick the sizes you sell. You can change these later on the product page.</p>
          <div className="space-y-3">
            {fields.map((f, i) => (
              <div key={f.id} className="grid items-start gap-3 sm:grid-cols-[6rem_1fr_1fr]">
                <Controller
                  control={control}
                  name={`variants.${i}.enabled`}
                  render={({ field }) => (
                    <label className="flex h-9 items-center gap-2 text-sm font-medium">
                      <Checkbox checked={field.value} onCheckedChange={(c) => field.onChange(c === true)} aria-label={`Sell ${f.weight}`} />
                      {f.weight}
                    </label>
                  )}
                />
                <Field label="Price (₹)" htmlFor={`v-${i}-price`} error={errors.variants?.[i]?.price?.message}>
                  <Input id={`v-${i}-price`} inputMode="decimal" {...register(`variants.${i}.price`)} />
                </Field>
                <Field label="Stock quantity" htmlFor={`v-${i}-qty`} error={errors.variants?.[i]?.quantity?.message}>
                  <Input id={`v-${i}-qty`} inputMode="numeric" {...register(`variants.${i}.quantity`)} />
                </Field>
              </div>
            ))}
          </div>
        </Section>
      )}

      <Section title="Search engine (optional)">
        <div className="grid gap-4 sm:grid-cols-2">
          {text("seo_title", "SEO title")}
          {text("seo_description", "SEO description", { rows: 2 })}
        </div>
      </Section>

      {formError && (
        <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {formError}
        </p>
      )}
      <div className="sticky bottom-0 -mx-4 flex justify-end gap-2 border-t bg-background/95 p-3 backdrop-blur sm:-mx-6 sm:px-6">
        <Button type="button" variant="outline" onClick={() => router.push("/admin/products")}>
          Cancel
        </Button>
        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? "Saving…" : product ? "Save changes" : "Create product"}
        </Button>
      </div>
    </form>
  );
}
