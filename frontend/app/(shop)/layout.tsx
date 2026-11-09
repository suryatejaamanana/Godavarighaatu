import { Suspense } from "react";
import { AnnouncementBar } from "@/components/shop/announcement-bar";
import { SiteFooter } from "@/components/shop/site-footer";
import { SiteHeader } from "@/components/shop/site-header";

export default function ShopLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <a href="#main" className="sr-only z-50 bg-brand-gold px-4 py-2 focus:not-sr-only focus:absolute focus:left-2 focus:top-2">
        Skip to content
      </a>
      <Suspense>
        <AnnouncementBar />
        <SiteHeader />
      </Suspense>
      <main id="main" className="flex-1">
        {children}
      </main>
      <Suspense>
        <SiteFooter />
      </Suspense>
    </>
  );
}
