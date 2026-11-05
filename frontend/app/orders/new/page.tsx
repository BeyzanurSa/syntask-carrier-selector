import type { Metadata } from "next";

import { OrderForm } from "@/components/orders/order-form";
import { PageHeader } from "@/components/page-header";

export const metadata: Metadata = { title: "Yeni Sipariş · Carrier Selector" };

export default function NewOrderPage() {
  return (
    <>
      <PageHeader
        title="Yeni Sipariş"
        description="Taşıma siparişi girin ve en uygun taşıyıcıyı bulun"
      />
      <OrderForm />
    </>
  );
}
