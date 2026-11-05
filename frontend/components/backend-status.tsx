"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api/client";

type Status = "checking" | "ok" | "down";

const LABELS: Record<Status, string> = {
  checking: "Kontrol ediliyor…",
  ok: "Backend çalışıyor",
  down: "Backend'e ulaşılamıyor",
};

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    api
      .GET("/health")
      .then(({ data }) => setStatus(data?.status === "ok" ? "ok" : "down"))
      .catch(() => setStatus("down"));
  }, []);

  return (
    <Badge
      variant={status === "down" ? "destructive" : "secondary"}
      aria-live="polite"
    >
      <span
        aria-hidden
        className={
          status === "ok"
            ? "size-2 rounded-full bg-success"
            : status === "down"
              ? "size-2 rounded-full bg-current"
              : "size-2 rounded-full bg-muted-foreground"
        }
      />
      {LABELS[status]}
    </Badge>
  );
}
