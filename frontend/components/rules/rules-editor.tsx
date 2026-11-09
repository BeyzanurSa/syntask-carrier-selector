"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowDown, ArrowUp, CheckCircle2, Loader2, Lock } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api/client";
import { apiErrorMessage } from "@/lib/api/errors";
import type { RankingEntry, Rules } from "@/lib/api/types";
import { cn } from "@/lib/utils";

function move<T>(list: T[], from: number, to: number): T[] {
  const next = [...list];
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}

export function RulesEditor({ rules }: { rules: Rules }) {
  const router = useRouter();
  const [ranking, setRanking] = useState<RankingEntry[]>(rules.ranking);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const label = (name: string) => rules.labels[name] ?? name;
  const dirty = JSON.stringify(ranking) !== JSON.stringify(rules.ranking);
  const noneEnabled = !ranking.some((r) => r.enabled);

  // Leaving the page with an unsaved order would silently discard it.
  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function update(next: RankingEntry[]) {
    setRanking(next);
    setSaved(false);
    setError(null);
  }

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const { error: apiError } = await api.PUT("/rules", {
        body: { constraints: rules.constraints, ranking, thresholds: rules.thresholds },
      });
      if (apiError) {
        setError(apiErrorMessage(apiError));
      } else {
        setSaved(true);
        router.refresh();
      }
    } catch {
      setError("Backend'e ulaşılamadı.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_20rem]">
      <Card>
        <CardHeader>
          <CardTitle>Sıralama kriterleri</CardTitle>
          <CardDescription>
            Uygun firmalar bu sırayla karşılaştırılır; ilk kriterde eşitlik varsa bir sonrakine geçilir. Tüm kriterler
            eşitse firma adı belirler.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="divide-y rounded-lg border">
            {ranking.map((entry, index) => (
              <li
                key={entry.name}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 transition-colors",
                  !entry.enabled && "text-muted-foreground bg-muted/40",
                  entry.name !== rules.ranking[index]?.name && "bg-warning/10",
                )}
              >
                <span className="bg-secondary text-secondary-foreground flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-semibold tabular-nums">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="font-medium">{label(entry.name)}</div>
                  <code className="text-muted-foreground text-xs">{entry.name}</code>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`${label(entry.name)} yukarı taşı`}
                  disabled={index === 0}
                  onClick={() => update(move(ranking, index, index - 1))}
                >
                  <ArrowUp aria-hidden />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`${label(entry.name)} aşağı taşı`}
                  disabled={index === ranking.length - 1}
                  onClick={() => update(move(ranking, index, index + 1))}
                >
                  <ArrowDown aria-hidden />
                </Button>
                <Switch
                  aria-label={`${label(entry.name)} açık`}
                  checked={entry.enabled}
                  onCheckedChange={(on) =>
                    update(ranking.map((r) => (r.name === entry.name ? { ...r, enabled: on } : r)))
                  }
                />
              </li>
            ))}
          </ol>

          {noneEnabled && <p className="text-destructive text-sm">En az bir kriter açık olmalı.</p>}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {saved && (
            <Alert className="border-success/40 bg-success/5">
              <CheckCircle2 className="text-success" aria-hidden />
              <AlertTitle>Kaydedildi</AlertTitle>
              <AlertDescription>
                rules.yaml güncellendi; bir sonraki seçim bu sırayla yapılır.{" "}
                <Link href="/selections" className="text-primary underline-offset-4 hover:underline">
                  Bir seçimi tekrar çalıştırın
                </Link>
                .
              </AlertDescription>
            </Alert>
          )}

          <div className="flex flex-wrap items-center gap-2">
            <Button onClick={save} disabled={!dirty || noneEnabled || saving}>
              {saving && <Loader2 className="animate-spin" aria-hidden />}
              {saving ? "Kaydediliyor…" : "Kaydet"}
            </Button>
            <Button variant="outline" disabled={!dirty || saving} onClick={() => update(rules.ranking)}>
              Geri al
            </Button>
            {dirty && (
              <span role="status" className="text-foreground flex items-center gap-1.5 text-xs">
                <span aria-hidden className="bg-warning size-2 rounded-full" />
                Kaydedilmemiş değişiklik var
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="space-y-6">
        <Card size="sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="size-4" aria-hidden />
              Zorunlu koşullar
            </CardTitle>
            <CardDescription>Tüm firmalar bunları sağlamalı. Yalnızca rules.yaml üzerinden değişir.</CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="flex flex-wrap gap-2">
              {rules.constraints.map((name) => (
                <li key={name}>
                  <Badge variant="secondary">{label(name)}</Badge>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card size="sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="size-4" aria-hidden />
              Eşikler
            </CardTitle>
            <CardDescription>Jev confidence eşikleri. Yalnızca rules.yaml üzerinden değişir.</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 text-sm">
              <dt className="text-muted-foreground">Alan güveni (Choice)</dt>
              <dd className="tabular-nums">{rules.thresholds.field_confidence}</dd>
              <dt className="text-muted-foreground">Not uyarısı (Noul)</dt>
              <dd className="tabular-nums">{rules.thresholds.note_warning}</dd>
            </dl>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
