import { AlertTriangle, CheckCircle2, CircleSlash, MapPinOff, MessageCircleQuestion, PlugZap } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { SelectionResponse, SelectionStatus } from "@/lib/api/types";
import {
  CARGO_LABELS,
  DISTANCE_SOURCE_LABELS,
  FIELD_LABELS,
  STATUS_LABELS,
  formatConfidence,
  formatMiles,
  formatMoney,
} from "@/lib/format";
import { cn } from "@/lib/utils";

const STATUS_ICONS: Record<SelectionStatus, typeof CheckCircle2> = {
  selected: CheckCircle2,
  no_carrier: CircleSlash,
  unknown_route: MapPinOff,
  invalid_order: AlertTriangle,
  needs_review: MessageCircleQuestion,
  jev_unavailable: PlugZap,
};

export function SelectionResult({ result }: { result: SelectionResponse }) {
  const { order, selected_carrier: winner, distance } = result;
  const Icon = STATUS_ICONS[result.status];
  const ok = result.status === "selected";

  return (
    <section aria-label="Seçim sonucu" className="space-y-6">
      <Alert className={cn(ok ? "border-success/40 bg-success/5" : "border-warning/50 bg-warning/10")}>
        <Icon className={ok ? "text-success" : "text-warning"} aria-hidden />
        <AlertTitle>{STATUS_LABELS[result.status]}</AlertTitle>
        <AlertDescription className="text-foreground">{result.reason}</AlertDescription>
      </Alert>
      {result.rules_used.length > 0 && (
        <p className="text-muted-foreground -mt-3 text-xs">
          Kullanılan sıralama: <code>{result.rules_used.join(" → ")}</code>
        </p>
      )}

      {order && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Stat label="Seçilen firma" value={winner?.name ?? "—"} hint={winner?.headquarters_city} />
          <Stat label="Toplam ücret" value={formatMoney(result.total_cost)} />
          <Stat
            label="Rota mesafesi"
            value={distance ? formatMiles(distance.miles) : "Bilinmiyor"}
            hint={`${order.origin} → ${order.destination}`}
            badge={distance ? DISTANCE_SOURCE_LABELS[distance.source] : undefined}
          />
          <Stat label="Sipariş" value={`${order.container_size} ft`} hint={CARGO_LABELS[order.cargo_type]} />
        </div>
      )}

      {result.confidence.source === "text" && Object.keys(result.confidence.fields).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Jev yorumu</CardTitle>
            <CardDescription>
              Serbest metinden okunan alanlar ve güven değerleri · en zayıf alan:{" "}
              <span className="tabular-nums">{formatConfidence(result.confidence.min)}</span>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Alan</TableHead>
                  <TableHead>Jev&apos;in okuduğu</TableHead>
                  <TableHead className="text-right">Güven</TableHead>
                  <TableHead>Durum</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(result.confidence.fields).map(([field, f]) => (
                  <TableRow key={field}>
                    <TableCell>{FIELD_LABELS[field] ?? field}</TableCell>
                    <TableCell className="font-medium">{f.value ?? "—"}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatConfidence(f.confidence)}</TableCell>
                    <TableCell>
                      <Badge
                        className={cn(
                          "border-transparent",
                          f.accepted ? "bg-success/10 text-success" : "bg-warning/15 text-foreground",
                        )}
                      >
                        {f.accepted ? "Kabul" : "Onay gerekli"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {result.eligible_carriers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Diğer uygun firmalar</CardTitle>
            <CardDescription>Tüm zorunlu koşulları sağlayan ama sıralamada geride kalan firmalar</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Firma</TableHead>
                  <TableHead className="text-right">Toplam ücret</TableHead>
                  <TableHead className="text-right">Merkez → çıkış</TableHead>
                  <TableHead>Neden geride</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {result.eligible_carriers.map((c) => (
                  <TableRow key={c.name}>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatMoney(c.total_cost)}</TableCell>
                    <TableCell className="text-right tabular-nums">{formatMiles(c.hq_distance)}</TableCell>
                    <TableCell className="text-muted-foreground whitespace-normal">{c.lost_on}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {result.rejected_carriers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Elenen firmalar</CardTitle>
            <CardDescription>En az bir zorunlu koşulu sağlamayan firmalar ve tüm gerekçeleri</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="divide-y">
              {result.rejected_carriers.map((c) => (
                <li key={c.name} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0 sm:flex-row sm:gap-6">
                  <span className="font-medium sm:w-40 sm:shrink-0">{c.name}</span>
                  <ul className="text-muted-foreground list-disc space-y-0.5 pl-5 text-sm">
                    {c.reasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </section>
  );
}

function Stat({
  label,
  value,
  hint,
  badge,
}: {
  label: string;
  value: string;
  hint?: string;
  badge?: string;
}) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardDescription className="flex items-center justify-between gap-2">
          {label}
          {badge && <Badge variant="secondary">{badge}</Badge>}
        </CardDescription>
        <CardTitle className="text-xl tabular-nums">{value}</CardTitle>
        {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
      </CardHeader>
    </Card>
  );
}
