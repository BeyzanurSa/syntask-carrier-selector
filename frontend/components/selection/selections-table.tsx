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
          <TableHead className="hidden sm:table-cell">Tarih</TableHead>
          <TableHead>Rota</TableHead>
          <TableHead className="hidden md:table-cell">Konteyner / Yük</TableHead>
          <TableHead>Durum</TableHead>
          <TableHead className="hidden sm:table-cell">Seçilen firma</TableHead>
          <TableHead className="hidden text-right sm:table-cell">Ücret</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {selections.map((s) => (
          // The route link is stretched over the whole row, so any cell opens the record (one tab stop per row).
          <TableRow key={s.id} className="group relative cursor-pointer">
            <TableCell className="text-muted-foreground hidden tabular-nums sm:table-cell">
              {formatDateTime(s.created_at)}
            </TableCell>
            <TableCell className="font-medium whitespace-normal">
              <Link
                href={`/selections/${s.id}`}
                className="group-hover:text-primary rounded-sm after:absolute after:inset-0 focus-visible:outline-none focus-visible:after:rounded-md focus-visible:after:ring-2 focus-visible:after:ring-ring"
              >
                {s.origin ? (
                  `${s.origin} → ${s.destination}`
                ) : (
                  <span className="text-muted-foreground line-clamp-2 max-w-40 font-normal italic sm:line-clamp-1 sm:max-w-56">
                    “{s.input_text}”
                  </span>
                )}
              </Link>
              {/* On phones the carrier and price columns are hidden; show them under the route instead. */}
              <div className="text-muted-foreground text-xs font-normal sm:hidden">
                {s.selected_carrier_name ?? "—"} · {formatMoney(s.total_cost)}
              </div>
            </TableCell>
            <TableCell className="hidden md:table-cell">
              {s.container_size ? `${s.container_size} ft · ${s.cargo_types?.join(" + ")}` : "—"}
            </TableCell>
            <TableCell>
              <StatusBadge status={s.status} />
            </TableCell>
            <TableCell className="hidden sm:table-cell">{s.selected_carrier_name ?? "—"}</TableCell>
            <TableCell className="hidden text-right tabular-nums sm:table-cell">{formatMoney(s.total_cost)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
