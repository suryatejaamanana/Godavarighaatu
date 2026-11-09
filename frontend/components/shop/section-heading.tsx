import Link from "next/link";

export function SectionHeading({
  title,
  titleTe,
  href,
  linkLabel = "View all",
}: {
  title: string;
  titleTe?: string;
  href?: string;
  linkLabel?: string;
}) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4">
      <div>
        <h2 className="font-display text-3xl font-semibold uppercase tracking-wide text-brand-red sm:text-4xl">{title}</h2>
        {titleTe && <p className="text-sm text-brand-brown/70">{titleTe}</p>}
        <span className="mt-1.5 block h-1 w-16 rounded-full bg-brand-gold" aria-hidden="true" />
      </div>
      {href && (
        <Link href={href} className="shrink-0 text-sm font-semibold text-brand-red underline-offset-4 hover:underline">
          {linkLabel} →
        </Link>
      )}
    </div>
  );
}
