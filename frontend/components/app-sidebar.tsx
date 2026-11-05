import { Suspense } from "react";
import { Truck } from "lucide-react";

import { ActiveNavLinks, NavLinks } from "@/components/nav-links";

export function AppSidebar() {
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
        {/* The active-item highlight depends on the URL; the plain links are prerendered. */}
        <Suspense fallback={<NavLinks pathname={null} />}>
          <ActiveNavLinks />
        </Suspense>
      </nav>
    </aside>
  );
}
