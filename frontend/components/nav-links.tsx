"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ListChecks,
  PackagePlus,
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

function isActive(pathname: string | null, href: string) {
  if (pathname === null) return false;
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}

/** The menu links; `pathname` null renders them without an active item (the prerendered shell). */
export function NavLinks({ pathname }: { pathname: string | null }) {
  return (
    <>
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
    </>
  );
}

/** Reads the current URL, so it must render inside <Suspense>. */
export function ActiveNavLinks() {
  return <NavLinks pathname={usePathname()} />;
}
