import Link from "next/link";

import { BackendStatus } from "@/components/backend-status";
import { PageHeader } from "@/components/page-header";
import { SelectionsTable } from "@/components/selection/selections-table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchSelections } from "@/lib/api/server";

export default async function DashboardPage() {
  const recent = await fetchSelections(8);

  return (
    <>
      <PageHeader title="Dashboard" description="Taşıyıcı ağı ve son seçimlerin özeti" />
      <div className="grid gap-6 xl:grid-cols-[1fr_18rem]">
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
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Sistem durumu</CardTitle>
            <CardDescription>Backend bağlantısı</CardDescription>
          </CardHeader>
          <CardContent>
            <BackendStatus />
          </CardContent>
        </Card>
      </div>
    </>
  );
}
