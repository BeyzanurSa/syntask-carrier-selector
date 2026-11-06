"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { CityInput } from "@/components/city-input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api/client";
import { apiErrorMessage } from "@/lib/api/errors";
import {
  CARGO_TYPES,
  CONTAINER_SIZES,
  type CargoType,
  type Carrier,
  type CarrierIn,
  type ContainerSize,
} from "@/lib/api/types";
import { CARGO_LABELS } from "@/lib/format";

type FormState = {
  name: string;
  headquartersCity: string;
  minDistance: string;
  maxDistance: string;
  sizes: ContainerSize[];
  cargoTypes: CargoType[];
  pricePerMile: string;
  isActive: boolean;
  description: string;
  reliability: string; // percent 0–100 in the form, stored as 0–1 in attributes.reliability
  attributes: string; // any other attributes, as JSON
};

function toForm(carrier?: Carrier): FormState {
  return {
    name: carrier?.name ?? "",
    headquartersCity: carrier?.headquarters_city ?? "",
    minDistance: carrier?.min_distance?.toString() ?? "",
    maxDistance: carrier?.max_distance?.toString() ?? "",
    sizes: carrier?.supported_container_sizes ?? [],
    cargoTypes: carrier?.supported_cargo_types ?? [],
    pricePerMile: carrier?.price_per_mile ?? "",
    isActive: carrier?.is_active ?? true,
    description: carrier?.description ?? "",
    ...splitReliability(carrier?.attributes ?? {}),
  };
}

function splitReliability(attributes: Record<string, unknown>): { reliability: string; attributes: string } {
  const { reliability, ...rest } = attributes;
  return {
    reliability: typeof reliability === "number" ? String(Math.round(reliability * 100)) : "",
    attributes: Object.keys(rest).length ? JSON.stringify(rest, null, 2) : "",
  };
}

/** Build the API payload, or return a message for problems the backend cannot see (bad JSON). */
function toPayload(form: FormState): CarrierIn | string {
  let attributes: Record<string, unknown> = {};
  if (form.attributes.trim()) {
    try {
      attributes = JSON.parse(form.attributes);
    } catch {
      return "Ek özellikler geçerli bir JSON nesnesi olmalı.";
    }
    if (typeof attributes !== "object" || attributes === null || Array.isArray(attributes)) {
      return "Ek özellikler bir JSON nesnesi olmalı, ör. {\"reliability\": 0.9}";
    }
  }
  if (form.reliability.trim() !== "") {
    const percent = Number(form.reliability);
    if (!Number.isFinite(percent) || percent < 0 || percent > 100) return "Güvenilirlik 0 ile 100 arasında olmalı.";
    attributes = { ...attributes, reliability: percent / 100 };
  } else {
    delete attributes.reliability;
  }
  const optionalInt = (value: string) => (value.trim() === "" ? null : Number(value));
  return {
    name: form.name,
    headquarters_city: form.headquartersCity,
    min_distance: optionalInt(form.minDistance),
    max_distance: optionalInt(form.maxDistance),
    supported_container_sizes: form.sizes,
    supported_cargo_types: form.cargoTypes,
    price_per_mile: form.pricePerMile,
    is_active: form.isActive,
    description: form.description.trim() || null,
    attributes,
  };
}

function toggle<T>(list: T[], value: T, on: boolean): T[] {
  return on ? [...list, value] : list.filter((v) => v !== value);
}

export function CarrierFormDialog({
  carrier,
  open,
  onOpenChange,
  onSaved,
}: {
  carrier?: Carrier;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: (name: string, warnings: string[]) => void;
}) {
  const [form, setForm] = useState<FormState>(() => toForm(carrier));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => setForm((f) => ({ ...f, [key]: value }));

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = toPayload(form);
    if (typeof payload === "string") {
      setError(payload);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const { data, error: apiError } = carrier
        ? await api.PUT("/carriers/{carrier_id}", { params: { path: { carrier_id: carrier.id } }, body: payload })
        : await api.POST("/carriers", { body: payload });
      if (apiError || !data) {
        setError(apiErrorMessage(apiError));
      } else {
        onSaved(data.name, data.warnings ?? []);
        onOpenChange(false);
      }
    } catch {
      setError("Backend'e ulaşılamadı.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{carrier ? `${carrier.name} düzenle` : "Yeni taşıyıcı"}</DialogTitle>
          <DialogDescription>Zorunlu koşullar seçimi belirler; açıklama yalnızca bilgi ve uyarı içindir.</DialogDescription>
        </DialogHeader>

        <form id="carrier-form" onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
          <Field id="name" label="Firma adı">
            <Input id="name" required value={form.name} onChange={(e) => set("name", e.target.value)} />
          </Field>
          <Field id="hq" label="Merkez şehir">
            <CityInput
              id="hq"
              required
              value={form.headquartersCity}
              onChange={(value) => set("headquartersCity", value)}
            />
          </Field>
          <Field id="min" label="Min. mesafe (mil)" hint="Boş = alt sınır yok">
            <Input id="min" type="number" min={0} value={form.minDistance} onChange={(e) => set("minDistance", e.target.value)} />
          </Field>
          <Field id="max" label="Maks. mesafe (mil)" hint="Boş = sınırsız">
            <Input id="max" type="number" min={0} value={form.maxDistance} onChange={(e) => set("maxDistance", e.target.value)} />
          </Field>

          <fieldset className="grid gap-2">
            <legend className="mb-1 text-sm font-medium">Konteyner boyutları</legend>
            {CONTAINER_SIZES.map((size) => (
              <label key={size} className="flex items-center gap-2 text-sm">
                <Checkbox
                  aria-label={`${size} ft`}
                  checked={form.sizes.includes(size)}
                  onCheckedChange={(on) => set("sizes", toggle(form.sizes, size, on))}
                />
                {size} ft
              </label>
            ))}
          </fieldset>
          <fieldset className="grid gap-2">
            <legend className="mb-1 text-sm font-medium">Yük tipleri</legend>
            {CARGO_TYPES.map((cargo) => (
              <label key={cargo} className="flex items-center gap-2 text-sm">
                <Checkbox
                  aria-label={CARGO_LABELS[cargo]}
                  checked={form.cargoTypes.includes(cargo)}
                  onCheckedChange={(on) => set("cargoTypes", toggle(form.cargoTypes, cargo, on))}
                />
                {CARGO_LABELS[cargo]}
              </label>
            ))}
          </fieldset>

          <Field id="price" label="Mil başına ücret ($)">
            <Input
              id="price"
              required
              type="number"
              step="0.01"
              min="0.01"
              value={form.pricePerMile}
              onChange={(e) => set("pricePerMile", e.target.value)}
            />
          </Field>
          <div className="flex items-end gap-2 pb-1.5">
            <Switch id="active" aria-label="Aktif" checked={form.isActive} onCheckedChange={(on) => set("isActive", on)} />
            <Label htmlFor="active">Aktif</Label>
          </div>

          <Field id="reliability" label="Güvenilirlik (%)" hint="Boş = puan yok; kriter açıksa sona kalır">
            <Input
              id="reliability"
              type="number"
              min={0}
              max={100}
              step={1}
              placeholder="ör. 92"
              value={form.reliability}
              onChange={(e) => set("reliability", e.target.value)}
            />
          </Field>
          <div className="hidden sm:block" aria-hidden />

          <Field id="description" label="Açıklama (serbest metin)" className="sm:col-span-2">
            <Textarea
              id="description"
              rows={3}
              placeholder="ör. Hafta sonu Hazardous yük kabul etmiyoruz."
              value={form.description}
              onChange={(e) => set("description", e.target.value)}
            />
          </Field>
          <Field id="attributes" label="Ek özellikler (JSON, opsiyonel)" className="sm:col-span-2">
            <Textarea
              id="attributes"
              rows={2}
              className="font-mono text-xs"
              placeholder='{"on_time_rate": 0.97}'
              value={form.attributes}
              onChange={(e) => set("attributes", e.target.value)}
            />
          </Field>
        </form>

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Vazgeç
          </Button>
          <Button type="submit" form="carrier-form" disabled={saving}>
            {saving && <Loader2 className="animate-spin" aria-hidden />}
            Kaydet
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({
  id,
  label,
  hint,
  className,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`grid gap-1.5 ${className ?? ""}`}>
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
    </div>
  );
}
