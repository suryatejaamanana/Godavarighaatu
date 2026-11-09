import { Skeleton } from "@/components/ui/skeleton";

export function ListingSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading pickles">
      <div className="mb-5 flex gap-2">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-10 w-24 rounded-full" />
        ))}
      </div>
      <ul className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
        {Array.from({ length: 8 }, (_, i) => (
          <li key={i}>
            <Skeleton className="aspect-[3/4] w-full rounded-2xl" />
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ProductSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading product" className="grid gap-8 md:grid-cols-2">
      <Skeleton className="aspect-square w-full rounded-2xl" />
      <div className="space-y-4">
        <Skeleton className="h-10 w-3/4" />
        <Skeleton className="h-6 w-1/3" />
        <Skeleton className="h-32 w-full" />
      </div>
    </div>
  );
}
