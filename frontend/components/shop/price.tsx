import { formatRupees } from "@/lib/format";
import { cn } from "@/lib/utils";

export function Price({
  price,
  compareAt,
  prefix,
  className,
}: {
  price: string;
  compareAt?: string | null;
  prefix?: string;
  className?: string;
}) {
  const discounted = compareAt && Number(compareAt) > Number(price);
  return (
    <p className={cn("flex flex-wrap items-baseline gap-x-2", className)}>
      {prefix && <span className="text-xs text-muted-foreground">{prefix}</span>}
      <span className="font-display text-xl font-semibold text-brand-red">{formatRupees(price)}</span>
      {discounted && (
        <s className="text-sm text-muted-foreground" aria-label={`Original price ${formatRupees(compareAt)}`}>
          {formatRupees(compareAt)}
        </s>
      )}
    </p>
  );
}
