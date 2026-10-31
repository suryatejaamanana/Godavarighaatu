"use client";

import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { PageHeader } from "@/components/admin/page-header";
import { ProductForm } from "@/components/admin/product-form";
import { useAdmin, useCan } from "@/hooks/use-admin";

export default function NewProductPage() {
  const { isPending } = useAdmin();
  const canEdit = useCan("manager");
  return (
    <>
      <Link href="/admin/products" className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="size-4" /> Products
      </Link>
      <PageHeader title="New product" />
      {!isPending && !canEdit ? (
        <p role="alert" className="rounded-lg border p-6 text-sm">You do not have permission to add products. Ask a manager.</p>
      ) : (
        <ProductForm />
      )}
    </>
  );
}
