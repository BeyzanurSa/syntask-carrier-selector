import {
  AlertTriangle,
  CheckCircle2,
  CircleSlash,
  Info,
  MapPinOff,
  MessageCircleQuestion,
  PlugZap,
  StickyNote,
  Trophy,
} from "lucide-react";

import Link from "next/link";

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
  const warned = new Set(result.warnings.map((w) => w.carrier));
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
          <Stat
            label="Seçilen firma"
            value={winner?.name ?? "—"}
            hint={winner?.headquarters_city}
            badge={winner && warned.has(winner.name) ? "Not uyarısı" : undefined}
            highlight={!!winner}
            icon={Trophy}
          />
          <Stat label="Toplam ücret" value={formatMoney(result.total_cost)} highlight={!!winner} />
          <Stat
            label="Rota mesafesi"
            value={distance ? formatMiles(distance.miles) : "Bilinmiyor"}
            hint={`${order.origin} → ${order.destination}`}
            badge={distance ? DISTANCE_SOURCE_LABELS[distance.source] : undefined}
          />
          <Stat
            label="Sipariş"
            value={`${order.container_size} ft`}
            hint={order.cargo_types.map((t) => CARGO_LABELS[t]).join(" + ")}
          />
        </div>
      )}

      {result.review && (
        <Card>
          <CardHeader>
            <CardTitle>Jev&apos;in sorusu</CardTitle>
            <CardDescription>{result.review.question}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {Object.keys(result.review.suggestions).length > 0 && (
              <p>
                <span className="text-muted-foreground">Jev&apos;in okudukları: </span>
                {Object.entries(result.review.suggestions)
                  .map(([field, value]) => `${FIELD_LABELS[field] ?? field}: ${value}`)
                  .join(" · ")}
              </p>
            )}
            <Link
              href={`/orders/new?${new URLSearchParams(result.review.suggestions).toString()}`}
              className="text-primary inline-block font-medium underline-offset-4 hover:underline"
            >
              Formda düzelt ve taşıyıcı bul →
            </Link>
          </CardContent>
        </Card>
      )}

      {result.warnings.length > 0 && (
        <Alert className="border-warning/50 bg-warning/10">
          <StickyNote className="text-warning" aria-hidden />
          <AlertTitle>Firma notu uyarısı</AlertTitle>
          <AlertDescription className="text-foreground space-y-2">
            <p className="text-muted-foreground text-xs">
              Jev bu notların sipariş için önemli olabileceğini düşünüyor. Seçimi değiştirmez; gerekirse firmayı
              arayın.
            </p>
            <ul className="space-y-1.5">
              {result.warnings.map((w) => (
                <li key={w.carrier}>
                  <span className="font-medium">{w.carrier}</span>{" "}
                  <span className="text-muted-foreground text-xs tabular-nums">(olasılık {w.probability.toFixed(2)})</span>
                  : “{w.note}”
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
      {!result.notes_checked && (
        <p className="text-muted-foreground flex items-center gap-1.5 text-xs">
          <Info className="size-3.5" aria-hidden />
          Firma notları kontrol edilemedi (Jev&apos;e ulaşılamadı); uyarı listesi eksik olabilir.
        </p>
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
                    <TableCell className="font-medium">
                      {c.name}
                      {warned.has(c.name) && (
                        <StickyNote className="text-warning ml-1.5 inline size-3.5" aria-label="Not uyarısı var" />
                      )}
                    </TableCell>
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
  highlight,
  icon: StatIcon,
}: {
  label: string;
  value: string;
  hint?: string;
  badge?: string;
  /** The answer itself (winner and price): stands out from the context cards. */
  highlight?: boolean;
  icon?: typeof Trophy;
}) {
  return (
    <Card size="sm" className={cn(highlight && "ring-primary/40 bg-primary/[0.03] ring-2")}>
      <CardHeader>
        <CardDescription className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5">
            {StatIcon && <StatIcon className="text-primary size-3.5" aria-hidden />}
            {label}
          </span>
          {badge && <Badge variant="secondary">{badge}</Badge>}
        </CardDescription>
        <CardTitle className={cn("font-semibold tabular-nums", highlight ? "group-data-[size=sm]/card:text-2xl" : "group-data-[size=sm]/card:text-xl")}>{value}</CardTitle>
        {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
      </CardHeader>
    </Card>
  );
}
