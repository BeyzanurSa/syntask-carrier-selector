"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CornerDownLeft, Eraser, Loader2, MessageCircleQuestion, Sparkles } from "lucide-react";

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

const MODES: { value: Mode; label: string }[] = [
  { value: "text", label: "Serbest metin" },
  { value: "form", label: "Form" },
];

/** One click fills the text box; they cover the main outcomes (selected, review, multi-cargo). */
const EXAMPLES = [
  { label: "Miami → Orlando, 40 ft kuru", text: "Miami'den Orlando'ya 40'lık kuru yük konteyneri taşınacak." },
  { label: "Jacksonville → Savannah, 45 ft", text: "Jacksonville'den Savannah'a 45 ft dry konteyner gönderilecek." },
  { label: "Boyut belirtilmemiş (inceleme)", text: "Need a reefer box from Ft. Lauderdale to Miami asap" },
  {
    label: "Soğutmalı + tehlikeli",
    text: "Miami'den Fort Lauderdale'e 20'lik soğutmalı tehlikeli madde konteyneri.",
  },
];

type FieldErrors = Partial<Record<"containerSize" | "cargoTypes", string>>;

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
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const resultRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<Record<Mode, HTMLButtonElement | null>>({ text: null, form: null });

  // Bring a new result into view and move focus to it, so keyboard and screen-reader users land on it too.
  useEffect(() => {
    if (!result) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    resultRef.current?.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    resultRef.current?.focus({ preventScroll: true });
  }, [result]);

  const uncertain = new Set(review?.review?.fields ?? []);
  const set = <K extends keyof Fields>(key: K, value: Fields[K]) => {
    setFields((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key]: undefined }));
  };
  const hasInput = fields.origin || fields.destination || fields.containerSize !== "" || fields.cargoTypes.length > 0;

  function clearForm() {
    setFields(fieldsFrom({}));
    setFieldErrors({});
    setReview(null);
    setError(null);
  }

  function onTabKey(event: React.KeyboardEvent) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    const next: Mode = mode === "text" ? "form" : "text";
    setMode(next);
    tabRefs.current[next]?.focus();
  }

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
    const errors: FieldErrors = {
      containerSize: fields.containerSize === "" ? "Konteyner boyutunu seçin." : undefined,
      cargoTypes: fields.cargoTypes.length === 0 ? "En az bir yük tipi seçin." : undefined,
    };
    if (fields.containerSize === "" || errors.cargoTypes) {
      setFieldErrors(errors);
      document.getElementById(errors.containerSize ? "container-size" : "cargo-types")?.focus();
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
          <div
            role="tablist"
            aria-label="Giriş türü"
            onKeyDown={onTabKey}
            className="bg-muted mt-2 inline-flex w-fit rounded-lg p-1"
          >
            {MODES.map(({ value, label }) => (
              <button
                key={value}
                ref={(el) => {
                  tabRefs.current[value] = el;
                }}
                role="tab"
                type="button"
                aria-selected={mode === value}
                tabIndex={mode === value ? 0 : -1}
                onClick={() => setMode(value)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm transition-colors focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
                  mode === value
                    ? "bg-card text-primary ring-border font-medium shadow-sm ring-1"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </CardHeader>
        <CardContent>
          {mode === "text" ? (
            <form onSubmit={submitText} aria-busy={submitting} className="grid gap-3">
              <Label htmlFor="order-text">Sipariş metni</Label>
              <Textarea
                id="order-text"
                required
                rows={3}
                aria-describedby="order-text-help"
                placeholder="Çıkış ve varış şehri, konteyner boyutu (20/40/45 ft) ve yük tipini yazın."
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    e.currentTarget.form?.requestSubmit();
                  }
                }}
              />
              <div id="order-text-help" className="flex flex-wrap items-center gap-1.5">
                <span className="text-muted-foreground text-xs">Örnekler:</span>
                {EXAMPLES.map((example) => (
                  <button
                    key={example.label}
                    type="button"
                    title={example.text}
                    onClick={() => setText(example.text)}
                    className="bg-secondary text-secondary-foreground hover:bg-accent focus-visible:ring-ring rounded-full px-2.5 py-1 text-xs transition-colors focus-visible:ring-2 focus-visible:outline-none"
                  >
                    {example.label}
                  </button>
                ))}
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button type="submit" disabled={submitting || !text.trim()}>
                  {submitting ? <Loader2 className="animate-spin" aria-hidden /> : <Sparkles aria-hidden />}
                  {submitting ? "Jev yorumluyor…" : "Jev ile yorumla ve taşıyıcı bul"}
                </Button>
                <span className="text-muted-foreground hidden items-center gap-1 text-xs sm:inline-flex">
                  <kbd className="bg-muted rounded border px-1 font-sans">⌘/Ctrl</kbd>+
                  <kbd className="bg-muted inline-flex items-center rounded border px-1">
                    <CornerDownLeft className="size-3" aria-label="Enter" />
                  </kbd>
                  ile gönder
                </span>
              </div>
            </form>
          ) : (
            <form onSubmit={submitFields} aria-busy={submitting} className="grid gap-4 sm:grid-cols-2">
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
              <Field
                id="container-size"
                label="Konteyner boyutu"
                hint={hintFor("container_size", review)}
                error={fieldErrors.containerSize}
              >
                <select
                  id="container-size"
                  aria-required
                  className={cn(
                    SELECT_CLASS,
                    fieldErrors.containerSize && "border-destructive aria-invalid:border-destructive aria-invalid:ring-destructive/30",
                  )}
                  aria-invalid={uncertain.has("container_size") || !!fieldErrors.containerSize || undefined}
                  aria-describedby={fieldErrors.containerSize ? "container-size-error" : undefined}
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
                  fieldErrors.cargoTypes && "ring-destructive/40 ring-3 ring-offset-4",
                )}
                aria-describedby={fieldErrors.cargoTypes ? "cargo-types-error" : undefined}
              >
                <legend className="mb-1 text-sm font-medium">Yük tipi</legend>
                <div id="cargo-types" tabIndex={-1} className="flex flex-wrap gap-x-4 gap-y-2 outline-none">
                  {CARGO_TYPES.map((cargo) => (
                    <label key={cargo} className="flex cursor-pointer items-center gap-2 py-0.5 text-sm">
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
                {fieldErrors.cargoTypes && (
                  <p id="cargo-types-error" role="alert" className="text-destructive text-xs font-medium">
                    {fieldErrors.cargoTypes}
                  </p>
                )}
                <p className="text-muted-foreground text-xs">
                  {hintFor("cargo_type", review) ??
                    "Birden fazla seçilebilir (ör. soğutmalı tehlikeli madde); firma hepsini desteklemeli."}
                </p>
              </fieldset>
              <div className="flex flex-wrap items-center gap-3 sm:col-span-2">
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="animate-spin" aria-hidden />}
                  {submitting ? "Hesaplanıyor…" : review ? "Onayla ve taşıyıcı bul" : "En uygun taşıyıcıyı bul"}
                </Button>
                {hasInput && (
                  <Button type="button" variant="ghost" onClick={clearForm} disabled={submitting}>
                    <Eraser aria-hidden />
                    Temizle
                  </Button>
                )}
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
          {error && (
            <Alert variant="destructive" role="alert" className="mt-4">
              <AlertTitle>İstek başarısız</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {result && (
        <div ref={resultRef} tabIndex={-1} className="scroll-mt-6 space-y-3 outline-none">
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
  error,
  children,
}: {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid content-start gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-destructive text-xs font-medium">
          {error}
        </p>
      )}
      {hint && <p className="text-muted-foreground text-xs">{hint}</p>}
    </div>
  );
}
