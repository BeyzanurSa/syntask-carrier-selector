import type { Metadata } from "next";

import { PageHeader } from "@/components/page-header";
import { SelectionsTable } from "@/components/selection/selections-table";
import { Card, CardContent } from "@/components/ui/card";
import { fetchSelections } from "@/lib/api/server";

export const metadata: Metadata = { title: "Seçim Sonuçları · Carrier Selector" };

export default async function SelectionsPage() {
  const selections = await fetchSelections(100);

  return (
    <>
      <PageHeader title="Seçim Sonuçları" description="Geçmiş taşıyıcı seçimleri ve gerekçeleri" />
      <Card>
        <CardContent>
          <SelectionsTable selections={selections} />
        </CardContent>
      </Card>
    </>
  );
}
