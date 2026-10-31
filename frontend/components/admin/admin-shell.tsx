"use client";

import { useQueryClient } from "@tanstack/react-query";
import { Boxes, LayoutDashboard, LogOut, Menu, Package, Tags } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Brand } from "@/components/admin/brand";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdmin } from "@/hooks/use-admin";
import { cn } from "@/lib/utils";
import { logout } from "@/services/admin";

const NAV = [
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/products", label: "Products", icon: Package },
  { href: "/admin/categories", label: "Categories", icon: Tags },
  { href: "/admin/inventory", label: "Inventory", icon: Boxes },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <nav className="flex flex-col gap-1 p-3">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-brand-cream/80 transition-colors hover:bg-white/10",
              active && "bg-brand-gold text-brand-brown hover:bg-brand-gold",
            )}
          >
            <Icon className="size-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function AdminShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: admin, isError, isPending } = useAdmin();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    if (isError) router.replace("/admin/login");
  }, [isError, router]);

  async function onLogout() {
    await logout().catch(() => undefined);
    queryClient.clear();
    router.replace("/admin/login");
  }

  if (isPending || !admin) {
    return (
      <div className="p-6" aria-busy="true" aria-label="Loading">
        <Skeleton className="mb-4 h-10 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[15rem_1fr]">
      <aside className="hidden bg-brand-red lg:block">
        <div className="sticky top-0">
          <div className="border-b border-white/10 p-5">
            <Brand />
          </div>
          <NavLinks />
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMenuOpen(true)} aria-label="Open menu">
            <Menu />
          </Button>
          <div className="lg:hidden">
            <Brand light={false} />
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden text-right text-sm sm:block">
              <div className="font-medium leading-tight">{admin.full_name ?? admin.email}</div>
              {admin.full_name && <div className="text-xs text-muted-foreground">{admin.email}</div>}
            </div>
            <Badge variant="secondary" className="capitalize">
              {admin.role.replace("_", " ")}
            </Badge>
            <Button variant="outline" size="sm" onClick={onLogout}>
              <LogOut /> <span className="hidden sm:inline">Log out</span>
            </Button>
          </div>
        </header>
        <main className="min-w-0 flex-1 p-4 sm:p-6">{children}</main>
      </div>

      <Sheet open={menuOpen} onOpenChange={setMenuOpen}>
        <SheetContent side="left" className="w-64 border-0 bg-brand-red p-0">
          <SheetTitle className="sr-only">Menu</SheetTitle>
          <div className="border-b border-white/10 p-5">
            <Brand />
          </div>
          <NavLinks onNavigate={() => setMenuOpen(false)} />
        </SheetContent>
      </Sheet>
    </div>
  );
}
