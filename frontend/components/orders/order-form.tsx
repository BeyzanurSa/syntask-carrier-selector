"use client";

import { useState } from "react";
import Link from "next/link";
import { Loader2, MessageCircleQuestion, Sparkles } from "lucide-react";

import { SelectionResult } from "@/components/selection/selection-result";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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

type Fields = { origin: string; destination: string; containerSize: ContainerSize | ""; cargoType: CargoType | "" };

const EMPTY_FIELDS: Fields = { origin: "", destination: "", containerSize: "", cargoType: "" };

/** Prefill the form from Jev's suggestions after a review or an unavailable Jev. */
function fieldsFrom(result: SelectionResponse): Fields {
  const s = result.review?.suggestions ?? {};
  const size = Number(s.container_size);
  return {
    origin: s.origin ?? "",
    destination: s.destination ?? "",
    containerSize: CONTAINER_SIZES.includes(size as ContainerSize) ? (size as ContainerSize) : "",
    cargoType: CARGO_TYPES.includes(s.cargo_type as CargoType) ? (s.cargo_type as CargoType) : "",
  };
}

export function OrderForm() {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [fields, setFields] = useState<Fields>(EMPTY_FIELDS);
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
        setFields(fieldsFrom(data));
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
    if (fields.containerSize === "" || fields.cargoType === "") {
      setError("Konteyner boyutu ve yük tipini seçin.");
      return;
    }
    submit({
      origin: fields.origin,
      destination: fields.destination,
      container_size: fields.containerSize,
      cargo_type: fields.cargoType,
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
                <Input
                  id="origin"
                  required
                  placeholder="örn. Miami"
                  aria-invalid={uncertain.has("origin") || undefined}
                  value={fields.origin}
                  onChange={(e) => set("origin", e.target.value)}
                />
              </Field>
              <Field id="destination" label="Varış şehri" hint={hintFor("destination", review)}>
                <Input
                  id="destination"
                  required
                  placeholder="örn. Orlando"
                  aria-invalid={uncertain.has("destination") || undefined}
                  value={fields.destination}
                  onChange={(e) => set("destination", e.target.value)}
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
              <Field id="cargo-type" label="Yük tipi" hint={hintFor("cargo_type", review)}>
                <select
                  id="cargo-type"
                  required
                  className={SELECT_CLASS}
                  aria-invalid={uncertain.has("cargo_type") || undefined}
                  value={fields.cargoType}
                  onChange={(e) => set("cargoType", e.target.value as CargoType)}
                >
                  <option value="" disabled>
                    Seçin…
                  </option>
                  {CARGO_TYPES.map((cargo) => (
                    <option key={cargo} value={cargo}>
                      {CARGO_LABELS[cargo]}
                    </option>
                  ))}
                </select>
              </Field>
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
