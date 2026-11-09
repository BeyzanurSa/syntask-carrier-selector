"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AlertTriangle, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { CarrierFormDialog } from "@/components/carriers/carrier-form-dialog";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { api } from "@/lib/api/client";
import { apiErrorMessage } from "@/lib/api/errors";
import type { Carrier, CarrierIn } from "@/lib/api/types";
import { formatMoney } from "@/lib/format";

function distanceRange(c: Carrier): string {
  if (c.min_distance == null && c.max_distance == null) return "Sınırsız";
  if (c.min_distance == null) return `≤ ${c.max_distance} mil`;
  if (c.max_distance == null) return `≥ ${c.min_distance} mil`;
  return `${c.min_distance}–${c.max_distance} mil`;
}

type Editing = { carrier?: Carrier; key: number } | null;

export function CarrierManager({ carriers }: { carriers: Carrier[] }) {
  const router = useRouter();
  const [editing, setEditing] = useState<Editing>(null);
  const [deleting, setDeleting] = useState<Carrier | null>(null);
  const [pending, setPending] = useState<Set<number>>(new Set());
  const [notice, setNotice] = useState<{ name: string; warnings: string[] } | null>(null);

  // Server Component data is re-fetched after every change.
  const refresh = () => router.refresh();

  async function setActive(carrier: Carrier, isActive: boolean) {
    setPending((ids) => new Set(ids).add(carrier.id));
    const body: CarrierIn = {
      name: carrier.name,
      headquarters_city: carrier.headquarters_city,
      min_distance: carrier.min_distance,
      max_distance: carrier.max_distance,
      supported_container_sizes: carrier.supported_container_sizes,
      supported_cargo_types: carrier.supported_cargo_types,
      price_per_mile: carrier.price_per_mile,
      is_active: isActive,
      description: carrier.description,
      attributes: carrier.attributes,
    };
    try {
      const { error: apiError } = await api.PUT("/carriers/{carrier_id}", {
        params: { path: { carrier_id: carrier.id } },
        body,
      });
      if (apiError) toast.error(apiErrorMessage(apiError));
      else
        toast.success(
          isActive ? `${carrier.name} aktif; seçimlere katılacak.` : `${carrier.name} pasif; seçimlerde dikkate alınmayacak.`,
        );
    } catch {
      toast.error("Backend'e ulaşılamadı.");
    }
    setPending((ids) => {
      const next = new Set(ids);
      next.delete(carrier.id);
      return next;
    });
    refresh();
  }

  async function confirmDelete() {
    if (!deleting) return;
    const name = deleting.name;
    try {
      const { error: apiError } = await api.DELETE("/carriers/{carrier_id}", {
        params: { path: { carrier_id: deleting.id } },
      });
      if (apiError) toast.error(apiErrorMessage(apiError));
      else toast.success(`${name} silindi. Geçmiş seçim kayıtları korunuyor.`);
    } catch {
      toast.error("Backend'e ulaşılamadı.");
    }
    setDeleting(null);
    refresh();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <p className="text-muted-foreground text-sm">
          {carriers.length} taşıyıcı · {carriers.filter((c) => c.is_active).length} aktif
        </p>
        <Button onClick={() => setEditing({ key: Date.now() })}>
          <Plus aria-hidden />
          Yeni taşıyıcı
        </Button>
      </div>

      {notice && notice.warnings.length > 0 && (
        <Alert className="border-warning/50 bg-warning/10">
          <AlertTriangle className="text-warning" aria-hidden />
          <AlertTitle>{notice.name} kaydedildi, bir uyarı var</AlertTitle>
          <AlertDescription className="text-foreground">
            {notice.warnings.map((w) => (
              <p key={w}>{w}</p>
            ))}
          </AlertDescription>
        </Alert>
      )}

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Firma</TableHead>
            <TableHead className="hidden sm:table-cell">Merkez</TableHead>
            <TableHead className="hidden md:table-cell">Mesafe</TableHead>
            <TableHead className="hidden md:table-cell">Konteyner</TableHead>
            <TableHead className="hidden lg:table-cell">Yük tipi</TableHead>
            <TableHead className="text-right">$/mil</TableHead>
            <TableHead className="hidden text-right xl:table-cell">Güvenilirlik</TableHead>
            <TableHead>Aktif</TableHead>
            <TableHead className="text-right">İşlemler</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {carriers.length === 0 && (
            <TableRow>
              <TableCell colSpan={9} className="text-muted-foreground py-10 text-center whitespace-normal">
                Henüz taşıyıcı yok. Seçim yapılabilmesi için en az bir aktif taşıyıcı ekleyin.
                <div className="mt-3">
                  <Button variant="outline" onClick={() => setEditing({ key: Date.now() })}>
                    <Plus aria-hidden />
                    İlk taşıyıcıyı ekle
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          )}
          {carriers.map((c) => (
            <TableRow key={c.id} className={c.is_active ? undefined : "text-muted-foreground"}>
              <TableCell className="max-w-64 whitespace-normal">
                <div className="font-medium">{c.name}</div>
                {c.description && <div className="text-muted-foreground line-clamp-2 text-xs">{c.description}</div>}
              </TableCell>
              <TableCell className="hidden sm:table-cell">{c.headquarters_city}</TableCell>
              <TableCell className="hidden md:table-cell">{distanceRange(c)}</TableCell>
              <TableCell className="hidden md:table-cell">{c.supported_container_sizes.join(", ")} ft</TableCell>
              <TableCell className="hidden lg:table-cell">
                <div className="flex flex-wrap gap-1">
                  {c.supported_cargo_types.map((t) => (
                    <Badge key={t} variant="secondary">
                      {t}
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell className="text-right tabular-nums">{formatMoney(c.price_per_mile)}</TableCell>
              <TableCell className="text-muted-foreground hidden text-right tabular-nums xl:table-cell">
                {typeof c.attributes?.reliability === "number" ? `%${Math.round(c.attributes.reliability * 100)}` : "—"}
              </TableCell>
              <TableCell>
                <Switch
                  checked={c.is_active}
                  disabled={pending.has(c.id)}
                  onCheckedChange={(on) => setActive(c, on)}
                  aria-label={`${c.name} aktif`}
                />
              </TableCell>
              <TableCell className="text-right">
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`${c.name} düzenle`}
                  onClick={() => setEditing({ carrier: c, key: Date.now() })}
                >
                  <Pencil aria-hidden />
                </Button>
                <Button variant="ghost" size="icon" aria-label={`${c.name} sil`} onClick={() => setDeleting(c)}>
                  <Trash2 className="text-destructive" aria-hidden />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {editing && (
        <CarrierFormDialog
          key={editing.key}
          carrier={editing.carrier}
          open
          onOpenChange={(open) => !open && setEditing(null)}
          onSaved={(name, warnings) => {
            setNotice({ name, warnings });
            if (warnings.length === 0) toast.success(`${name} kaydedildi.`);
            refresh();
          }}
        />
      )}

      <AlertDialog open={deleting !== null} onOpenChange={(open) => !open && setDeleting(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{deleting?.name} silinsin mi?</AlertDialogTitle>
            <AlertDialogDescription>
              Firma kalıcı olarak silinir. Geçmiş seçim kayıtları etkilenmez. Geçici olarak devre dışı bırakmak için
              &quot;Aktif&quot; anahtarını kullanın.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Vazgeç</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={confirmDelete}>
              Sil
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
