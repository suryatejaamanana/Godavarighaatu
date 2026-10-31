"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, ChevronLeft, RotateCcw } from "lucide-react";
import Link from "next/link";
import { use } from "react";
import { toast } from "sonner";
import { ImagesPanel } from "@/components/admin/images-panel";
import { PageHeader } from "@/components/admin/page-header";
import { ProductForm } from "@/components/admin/product-form";
import { ErrorState, LoadingRows } from "@/components/admin/query-state";
import { StatusBadge } from "@/components/admin/status-badge";
import { VariantsPanel } from "@/components/admin/variants-panel";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCan } from "@/hooks/use-admin";
import { archiveProduct, getProduct, restoreProduct } from "@/services/admin";

export default function EditProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const canEdit = useCan("manager");
  const queryClient = useQueryClient();
  const product = useQuery({ queryKey: ["product", id], queryFn: () => getProduct(id) });

  const toggleArchive = useMutation({
    mutationFn: () => (product.data?.status === "archived" ? restoreProduct(id) : archiveProduct(id)),
    onSuccess: (p) => {
      toast.success(p.status === "archived" ? "Product archived" : "Product restored as hidden");
      queryClient.invalidateQueries({ queryKey: ["product", id] });
      queryClient.invalidateQueries({ queryKey: ["products"] });
      queryClient.invalidateQueries({ queryKey: ["summary"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <>
      <Link href="/admin/products" className="mb-2 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ChevronLeft className="size-4" /> Products
      </Link>
      {product.isPending ? (
        <LoadingRows />
      ) : product.isError ? (
        <ErrorState error={product.error} onRetry={() => product.refetch()} />
      ) : (
        <>
          <PageHeader
            title={product.data.name}
            description={product.data.name_te ?? undefined}
            actions={
              <>
                <StatusBadge status={product.data.status} />
                {canEdit && (
                  <Button variant="outline" size="sm" disabled={toggleArchive.isPending} onClick={() => toggleArchive.mutate()}>
                    {product.data.status === "archived" ? <RotateCcw /> : <Archive />}
                    {product.data.status === "archived" ? "Restore" : "Archive"}
                  </Button>
                )}
              </>
            }
          />
          <Tabs defaultValue="details">
            <TabsList className="mb-4">
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="variants">Sizes &amp; stock ({product.data.variants.length})</TabsTrigger>
              <TabsTrigger value="images">Photos ({product.data.images.length})</TabsTrigger>
            </TabsList>
            <TabsContent value="details">
              {canEdit ? (
                <ProductForm key={`${product.data.id}-${product.dataUpdatedAt}`} product={product.data} />
              ) : (
                <p className="rounded-lg border p-6 text-sm text-muted-foreground">Only managers can edit product details. You can manage stock in the “Sizes &amp; stock” tab.</p>
              )}
            </TabsContent>
            <TabsContent value="variants">
              <VariantsPanel product={product.data} />
            </TabsContent>
            <TabsContent value="images">
              <ImagesPanel product={product.data} />
            </TabsContent>
          </Tabs>
        </>
      )}
    </>
  );
}
