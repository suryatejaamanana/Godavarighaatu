import { Badge } from "@/components/ui/badge";
import type { ProductStatus } from "@/types/api";

const LABEL: Record<ProductStatus, string> = { active: "Active", inactive: "Hidden", archived: "Archived" };

export function StatusBadge({ status }: { status: ProductStatus }) {
  return <Badge variant={status === "active" ? "default" : status === "archived" ? "destructive" : "secondary"}>{LABEL[status]}</Badge>;
}
