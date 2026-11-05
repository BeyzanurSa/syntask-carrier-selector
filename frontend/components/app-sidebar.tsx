"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  PackagePlus,
  ListChecks,
  SlidersHorizontal,
  Truck,
} from "lucide-react";

import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/carriers", label: "Taşıyıcılar", icon: Truck },
  { href: "/orders/new", label: "Yeni Sipariş", icon: PackagePlus },
  { href: "/selections", label: "Seçim Sonuçları", icon: ListChecks },
  { href: "/rules", label: "Kurallar", icon: SlidersHorizontal },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

export function AppSidebar() {
  const pathname = usePathname();

  return (
    <aside className="bg-sidebar text-sidebar-foreground flex shrink-0 flex-col md:min-h-screen md:w-60">
      <div className="flex items-center gap-2 px-5 py-4">
        <Truck className="size-5" aria-hidden />
        <span className="font-semibold tracking-tight">Carrier Selector</span>
      </div>
      <nav
        aria-label="Ana menü"
        className="flex gap-1 overflow-x-auto px-3 pb-3 md:flex-col md:overflow-visible"
      >
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            aria-current={isActive(pathname, href) ? "page" : undefined}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm whitespace-nowrap transition-colors",
              "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              isActive(pathname, href) &&
                "bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary hover:text-sidebar-primary-foreground",
            )}
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
