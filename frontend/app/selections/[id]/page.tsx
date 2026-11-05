import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { RerunButton } from "@/components/selection/rerun-button";
import { SelectionResult } from "@/components/selection/selection-result";
import { fetchSelection } from "@/lib/api/server";
import type { SelectCarrierRequest } from "@/lib/api/types";
import { formatDateTime } from "@/lib/format";

export async function generateMetadata(props: PageProps<"/selections/[id]">) {
  const { id } = await props.params;
  return { title: `Seçim #${id} · Carrier Selector` };
}

export default async function SelectionDetailPage(props: PageProps<"/selections/[id]">) {
  const { id } = await props.params;
  const selectionId = Number(id);
  if (!Number.isInteger(selectionId)) notFound();

  const record = await fetchSelection(selectionId);
  if (!record) notFound();

  return (
    <>
      <Link
        href="/selections"
        className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1 text-sm"
      >
        <ArrowLeft className="size-4" aria-hidden />
        Seçim sonuçları
      </Link>
      <PageHeader
        title={`Seçim #${record.id}`}
        description={formatDateTime(record.created_at)}
      />
      <div className="mb-6">
        <RerunButton input={record.input as SelectCarrierRequest} />
        <p className="text-muted-foreground mt-2 text-xs">
          Aynı siparişi güncel kurallarla yeniden çalıştırır ve yeni bir seçim kaydı oluşturur. Bu kayıt değişmez.
        </p>
      </div>
      <SelectionResult result={record.response} />
    </>
  );
}
