import type { Metadata } from "next";
import Link from "next/link";
import { PackagePlus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { SelectionsTable } from "@/components/selection/selections-table";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { fetchSelections } from "@/lib/api/server";

export const metadata: Metadata = { title: "Seçim Sonuçları · Carrier Selector" };

export default async function SelectionsPage() {
  const selections = await fetchSelections(100);

  return (
    <>
      <PageHeader
        title="Seçim Sonuçları"
        description="Geçmiş taşıyıcı seçimleri ve gerekçeleri · ayrıntı için bir satıra tıklayın"
        actions={
          <Link href="/orders/new" className={buttonVariants()}>
            <PackagePlus aria-hidden />
            Yeni sipariş
          </Link>
        }
      />
      <Card>
        <CardContent>
          <SelectionsTable selections={selections} />
        </CardContent>
      </Card>
    </>
  );
}
