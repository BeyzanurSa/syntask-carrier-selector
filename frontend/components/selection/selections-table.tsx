import Link from "next/link";

import { StatusBadge } from "@/components/selection/status-badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { SelectionSummary } from "@/lib/api/types";
import { formatDateTime, formatMoney } from "@/lib/format";

export function SelectionsTable({ selections }: { selections: SelectionSummary[] }) {
  if (selections.length === 0) {
    return (
      <p className="text-muted-foreground py-6 text-center text-sm">
        Henüz seçim yok.{" "}
        <Link href="/orders/new" className="text-primary underline-offset-4 hover:underline">
          İlk siparişi oluşturun
        </Link>
        .
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Tarih</TableHead>
          <TableHead>Rota</TableHead>
          <TableHead>Konteyner / Yük</TableHead>
          <TableHead>Durum</TableHead>
          <TableHead>Seçilen firma</TableHead>
          <TableHead className="text-right">Ücret</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {selections.map((s) => (
          <TableRow key={s.id}>
            <TableCell className="text-muted-foreground tabular-nums">
              <Link href={`/selections/${s.id}`} className="hover:text-foreground hover:underline">
                {formatDateTime(s.created_at)}
              </Link>
            </TableCell>
            <TableCell className="font-medium">
              <Link href={`/selections/${s.id}`} className="hover:underline">
                {s.origin} → {s.destination}
              </Link>
            </TableCell>
            <TableCell>
              {s.container_size} ft · {s.cargo_type}
            </TableCell>
            <TableCell>
              <StatusBadge status={s.status} />
            </TableCell>
            <TableCell>{s.selected_carrier_name ?? "—"}</TableCell>
            <TableCell className="text-right tabular-nums">{formatMoney(s.total_cost)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
