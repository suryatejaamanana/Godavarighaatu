import { cn } from "@/lib/utils";

/** Temporary stand-in shown until real product photographs are uploaded. */
export function PlaceholderArt({ className, label = "Photo coming soon" }: { className?: string; label?: string }) {
  return (
    <div
      role="img"
      aria-label={label}
      className={cn("flex size-full items-center justify-center bg-gradient-to-br from-brand-gold/40 via-brand-cream to-brand-orange/30", className)}
    >
      <svg viewBox="0 0 120 120" className="w-1/2 max-w-40 text-brand-red/70" aria-hidden="true">
        <rect x="34" y="14" width="52" height="12" rx="4" fill="currentColor" />
        <path d="M30 34h60c6 0 10 4 10 10v46c0 10-8 18-18 18H38c-10 0-18-8-18-18V44c0-6 4-10 10-10z" fill="none" stroke="currentColor" strokeWidth="6" />
        <circle cx="60" cy="68" r="14" fill="currentColor" opacity=".35" />
        <path d="M52 68c2-8 14-8 16 0-2 8-14 8-16 0z" fill="#FFC928" />
      </svg>
    </div>
  );
}
