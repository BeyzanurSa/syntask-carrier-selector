import Link from "next/link";

import { PageHeader } from "@/components/page-header";

export default function NotFound() {
  return (
    <>
      <PageHeader title="Sayfa bulunamadı" description="Aradığınız kayıt mevcut değil veya silinmiş olabilir." />
      <Link href="/" className="text-primary text-sm underline-offset-4 hover:underline">
        Dashboard&apos;a dön
      </Link>
    </>
  );
}
