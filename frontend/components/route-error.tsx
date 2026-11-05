"use client";

import { AlertTriangle } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

/** Shared body for route error boundaries: the backend is usually just not running. */
export function RouteError({ retry }: { retry: () => void }) {
  return (
    <Alert variant="destructive" className="max-w-xl">
      <AlertTriangle aria-hidden />
      <AlertTitle>Veriler yüklenemedi</AlertTitle>
      <AlertDescription className="space-y-3">
        <p>Backend&apos;e ulaşılamadı. Sunucunun çalıştığından emin olup tekrar deneyin.</p>
        <Button size="sm" variant="outline" onClick={() => retry()}>
          Tekrar dene
        </Button>
      </AlertDescription>
    </Alert>
  );
}
