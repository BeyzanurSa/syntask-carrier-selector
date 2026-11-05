"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { SelectionResult } from "@/components/selection/selection-result";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api/client";
import {
  CARGO_TYPES,
  CONTAINER_SIZES,
  type CargoType,
  type ContainerSize,
  type SelectionResponse,
} from "@/lib/api/types";
import { CARGO_LABELS } from "@/lib/format";

const SELECT_CLASS =
  "border-input h-8 w-full rounded-lg border bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50";

export function OrderForm() {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [containerSize, setContainerSize] = useState<ContainerSize>(40);
  const [cargoType, setCargoType] = useState<CargoType>("Dry");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SelectionResponse | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { data, error: apiError } = await api.POST("/select-carrier", {
        body: { origin, destination, container_size: containerSize, cargo_type: cargoType },
      });
      if (apiError || !data) {
        setResult(null);
        setError("Sipariş bilgileri geçersiz. Lütfen alanları kontrol edin.");
      } else {
        setResult(data);
      }
    } catch {
      setResult(null);
      setError("Backend'e ulaşılamadı. Sunucunun çalıştığından emin olun.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-8">
      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>Sipariş bilgileri</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
            <Field id="origin" label="Çıkış şehri">
              <Input
                id="origin"
                required
                placeholder="örn. Miami"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
              />
            </Field>
            <Field id="destination" label="Varış şehri">
              <Input
                id="destination"
                required
                placeholder="örn. Orlando"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
              />
            </Field>
            <Field id="container-size" label="Konteyner boyutu">
              <select
                id="container-size"
                className={SELECT_CLASS}
                value={containerSize}
                onChange={(e) => setContainerSize(Number(e.target.value) as ContainerSize)}
              >
                {CONTAINER_SIZES.map((size) => (
                  <option key={size} value={size}>
                    {size} ft
                  </option>
                ))}
              </select>
            </Field>
            <Field id="cargo-type" label="Yük tipi">
              <select
                id="cargo-type"
                className={SELECT_CLASS}
                value={cargoType}
                onChange={(e) => setCargoType(e.target.value as CargoType)}
              >
                {CARGO_TYPES.map((cargo) => (
                  <option key={cargo} value={cargo}>
                    {CARGO_LABELS[cargo]}
                  </option>
                ))}
              </select>
            </Field>
            <div className="sm:col-span-2">
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="animate-spin" aria-hidden />}
                En uygun taşıyıcıyı bul
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="max-w-3xl">
          <AlertTitle>İstek başarısız</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && <SelectionResult result={result} />}
    </div>
  );
}

function Field({ id, label, children }: { id: string; label: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  );
}
