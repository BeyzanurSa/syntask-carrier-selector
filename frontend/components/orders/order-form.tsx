"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Loader2, MessageCircleQuestion, Sparkles } from "lucide-react";

import { CityInput } from "@/components/city-input";
import { SelectionResult } from "@/components/selection/selection-result";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api/client";
import {
  CARGO_TYPES,
  CONTAINER_SIZES,
  type CargoType,
  type ContainerSize,
  type SelectCarrierRequest,
  type SelectionResponse,
} from "@/lib/api/types";
import { CARGO_LABELS, formatConfidence } from "@/lib/format";
import { cn } from "@/lib/utils";

const SELECT_CLASS =
  "border-input h-8 w-full rounded-lg border bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 aria-invalid:border-warning aria-invalid:ring-3 aria-invalid:ring-warning/30";

type Mode = "text" | "form";

type Fields = { origin: string; destination: string; containerSize: ContainerSize | ""; cargoTypes: CargoType[] };

/** Fields from Jev's suggestions (review) or from the "Formda düzelt" link on a review record. */
function fieldsFrom(s: Record<string, string | null | undefined>): Fields {
  const size = Number(s.container_size);
  return {
    origin: s.origin ?? "",
    destination: s.destination ?? "",
    containerSize: CONTAINER_SIZES.includes(size as ContainerSize) ? (size as ContainerSize) : "",
    cargoTypes: CARGO_TYPES.filter((t) => (s.cargo_type ?? "").split(",").includes(t)),
  };
}

export function OrderForm() {
  const params = useSearchParams();
  const prefilled = params.has("origin") || params.has("container_size") || params.has("cargo_type");
  const [mode, setMode] = useState<Mode>(prefilled ? "form" : "text");
  const [text, setText] = useState("");
  const [fields, setFields] = useState<Fields>(() => fieldsFrom(Object.fromEntries(params)));
  const [review, setReview] = useState<SelectionResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<SelectionResponse | null>(null);

  const uncertain = new Set(review?.review?.fields ?? []);
  const set = <K extends keyof Fields>(key: K, value: Fields[K]) => setFields((f) => ({ ...f, [key]: value }));

  async function submit(body: SelectCarrierRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const { data, error: apiError } = await api.POST("/select-carrier", { body });
      if (apiError || !data) {
        setResult(null);
        setError("Sipariş bilgileri geçersiz. Lütfen alanları kontrol edin.");
        return;
      }
      if (data.status === "needs_review" || data.status === "jev_unavailable") {
        // No carrier was assigned: hand over to the form, prefilled with whatever Jev could read.
        setReview(data);
        setFields(fieldsFrom(data.review?.suggestions ?? {}));
        setMode("form");
        setResult(null);
        return;
      }
      setReview(null);
      setResult(data);
    } catch {
      setResult(null);
      setError("Backend'e ulaşılamadı. Sunucunun çalıştığından emin olun.");
    } finally {
      setSubmitting(false);
    }
  }

  function submitText(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    submit({ text });
  }

  function submitFields(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (fields.containerSize === "" || fields.cargoTypes.length === 0) {
      setError("Konteyner boyutunu ve en az bir yük tipini seçin.");
      return;
    }
    submit({
      origin: fields.origin,
      destination: fields.destination,
      container_size: fields.containerSize,
      cargo_types: fields.cargoTypes,
    });
  }

  return (
    <div className="space-y-8">
      <Card className="max-w-3xl">
        <CardHeader>
          <CardTitle>Sipariş bilgileri</CardTitle>
          <CardDescription>
            Serbest metni Jev yorumlar; emin olmadığı alanlar için sizden onay istenir. Form ile girilen siparişler
            Jev&apos;e gitmez.
          </CardDescription>
          <div role="tablist" aria-label="Giriş türü" className="bg-muted mt-2 inline-flex w-fit rounded-lg p-1">
            {(["text", "form"] as const).map((m) => (
              <button
                key={m}
                role="tab"
                type="button"
                aria-selected={mode === m}
                onClick={() => setMode(m)}
                className={cn(
                  "rounded-md px-3 py-1 text-sm transition-colors",
                  mode === m ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground",
                )}
              >
                {m === "text" ? "Serbest metin" : "Form"}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {mode === "text" ? (
            <form onSubmit={submitText} className="grid gap-3">
              <Label htmlFor="order-text">Sipariş metni</Label>
              <Textarea
                id="order-text"
                required
                rows={3}
                placeholder="örn. Miami'den Orlando'ya 40'lık kuru yük konteyneri taşınacak."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <div>
                <Button type="submit" disabled={submitting || !text.trim()}>
                  {submitting ? <Loader2 className="animate-spin" aria-hidden /> : <Sparkles aria-hidden />}
                  Jev ile yorumla ve taşıyıcı bul
                </Button>
              </div>
            </form>
          ) : (
            <form onSubmit={submitFields} className="grid gap-4 sm:grid-cols-2">
              {review && (
                <Alert className="border-warning/50 bg-warning/10 sm:col-span-2">
                  <MessageCircleQuestion className="text-warning" aria-hidden />
                  <AlertTitle>
                    {review.status === "needs_review" ? "Onayınız gerekiyor" : "Jev kullanılamadı"}
                  </AlertTitle>
                  <AlertDescription className="text-foreground">
                    {review.review?.question ?? review.reason}
                  </AlertDescription>
                </Alert>
              )}
              <Field id="origin" label="Çıkış şehri" hint={hintFor("origin", review)}>
                <CityInput
                  id="origin"
                  required
                  placeholder="örn. Miami"
                  invalid={uncertain.has("origin")}
                  value={fields.origin}
                  onChange={(value) => set("origin", value)}
                />
              </Field>
              <Field id="destination" label="Varış şehri" hint={hintFor("destination", review)}>
                <CityInput
                  id="destination"
                  required
                  placeholder="örn. Orlando"
                  invalid={uncertain.has("destination")}
                  value={fields.destination}
                  onChange={(value) => set("destination", value)}
                />
              </Field>
              <Field id="container-size" label="Konteyner boyutu" hint={hintFor("container_size", review)}>
                <select
                  id="container-size"
                  required
                  className={SELECT_CLASS}
                  aria-invalid={uncertain.has("container_size") || undefined}
                  value={fields.containerSize}
                  onChange={(e) => set("containerSize", Number(e.target.value) as ContainerSize)}
                >
                  <option value="" disabled>
                    Seçin…
                  </option>
                  {CONTAINER_SIZES.map((size) => (
                    <option key={size} value={size}>
                      {size} ft
                    </option>
                  ))}
                </select>
              </Field>
              <fieldset
                className={cn(
                  "grid gap-1.5 rounded-lg",
                  uncertain.has("cargo_type") && "ring-warning/40 ring-3 ring-offset-4",
                )}
              >
                <legend className="mb-1 text-sm font-medium">Yük tipi</legend>
                <div className="flex flex-wrap gap-x-4 gap-y-1.5">
                  {CARGO_TYPES.map((cargo) => (
                    <label key={cargo} className="flex items-center gap-2 text-sm">
                      <Checkbox
                        aria-label={CARGO_LABELS[cargo]}
                        checked={fields.cargoTypes.includes(cargo)}
                        onCheckedChange={(on) =>
                          set(
                            "cargoTypes",
                            on ? [...fields.cargoTypes, cargo] : fields.cargoTypes.filter((t) => t !== cargo),
                          )
                        }
                      />
                      {CARGO_LABELS[cargo]}
                    </label>
                  ))}
                </div>
                <p className="text-muted-foreground text-xs">
                  {hintFor("cargo_type", review) ??
                    "Birden fazla seçilebilir (ör. soğutmalı tehlikeli madde); firma hepsini desteklemeli."}
                </p>
              </fieldset>
              <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="animate-spin" aria-hidden />}
                  {review ? "Onayla ve taşıyıcı bul" : "En uygun taşıyıcıyı bul"}
                </Button>
                {review?.selection_id != null && (
                  <Link
                    href={`/selections/${review.selection_id}`}
                    className="text-muted-foreground text-xs underline-offset-4 hover:underline"
                  >
                    İnceleme kaydı #{review.selection_id}
                  </Link>
                )}
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive" className="max-w-3xl">
          <AlertTitle>İstek başarısız</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {result && (
        <div className="space-y-3">
          {result.selection_id != null && (
            <Link
              href={`/selections/${result.selection_id}`}
              className="text-primary text-sm underline-offset-4 hover:underline"
            >
              Seçim kaydı #{result.selection_id} →
            </Link>
          )}
          <SelectionResult result={result} />
        </div>
      )}
    </div>
  );
}

/** "Jev: Orlando (0.40)" under a field Jev read, or nothing. */
function hintFor(field: string, review: SelectionResponse | null): string | undefined {
  const reading = review?.confidence.fields[field];
  if (!reading) return undefined;
  const value = reading.value === "unspecified" ? "belirtilmemiş" : reading.value === "other_city" ? "listede yok" : reading.value;
  return `Jev: ${value} (güven ${formatConfidence(reading.confidence)})${reading.accepted ? "" : " · onay gerekli"}`;
}

function Field({
  id,
  label,
  hint,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
    </div>
  );
}
