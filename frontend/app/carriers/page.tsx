import type { Metadata } from "next";

import { CarrierManager } from "@/components/carriers/carrier-manager";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { fetchCarriers } from "@/lib/api/server";

export const metadata: Metadata = { title: "Taşıyıcılar · Carrier Selector" };

export default async function CarriersPage() {
  const carriers = await fetchCarriers();

  return (
    <>
      <PageHeader title="Taşıyıcılar" description="Taşıyıcı firmaları ekleyin, düzenleyin ve yönetin" />
      <Card>
        <CardContent>
          <CarrierManager carriers={carriers} />
        </CardContent>
      </Card>
    </>
  );
}
