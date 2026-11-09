import Link from "next/link";
import { PackagePlus } from "lucide-react";

import { BackendStatus } from "@/components/backend-status";
import { PageHeader } from "@/components/page-header";
import { SelectionsTable } from "@/components/selection/selections-table";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchCarriers, fetchSelections } from "@/lib/api/server";

export default async function DashboardPage() {
  const [carriers, recent] = await Promise.all([fetchCarriers(), fetchSelections(8)]);
  const active = carriers.filter((c) => c.is_active).length;

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Taşıyıcı ağı ve son seçimlerin özeti"
        actions={
          <Link href="/orders/new" className={buttonVariants()}>
            <PackagePlus aria-hidden />
            Yeni sipariş
          </Link>
        }
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard label="Toplam taşıyıcı" value={carriers.length} href="/carriers" />
        <StatCard label="Aktif taşıyıcı" value={active} href="/carriers" />
        <Card size="sm">
          <CardHeader>
            <CardDescription>Sistem durumu</CardDescription>
            <div className="pt-1">
              <BackendStatus />
            </div>
          </CardHeader>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Son seçimler</CardTitle>
          <CardDescription>
            En son {recent.length} sipariş ·{" "}
            <Link href="/selections" className="text-primary underline-offset-4 hover:underline">
              Tümünü gör
            </Link>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SelectionsTable selections={recent} />
        </CardContent>
      </Card>
    </>
  );
}

function StatCard({ label, value, href }: { label: string; value: number; href: string }) {
  return (
    <Link href={href} className="rounded-xl focus-visible:outline-2">
      <Card size="sm" className="hover:ring-primary/30 h-full transition-shadow hover:ring-2">
        <CardHeader>
          <CardDescription>{label}</CardDescription>
          <CardTitle className="font-semibold tabular-nums group-data-[size=sm]/card:text-3xl">{value}</CardTitle>
        </CardHeader>
      </Card>
    </Link>
  );
}
