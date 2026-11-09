import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-dvh flex-1 flex-col items-center justify-center bg-brand-cream px-4 text-center">
      <p className="font-display text-7xl font-bold text-brand-red">404</p>
      <h1 className="mt-2 text-2xl font-bold">We could not find that page</h1>
      <p className="mt-2 max-w-md text-muted-foreground">The pickle or page you are looking for may have moved or is no longer available.</p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link href="/" className="inline-flex h-11 items-center rounded-full bg-brand-red px-6 font-semibold text-brand-cream">
          Go home
        </Link>
        <Link href="/products" className="inline-flex h-11 items-center rounded-full border-2 border-brand-red px-6 font-semibold text-brand-red">
          Browse pickles
        </Link>
      </div>
    </main>
  );
}
