"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, RotateCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { api } from "@/lib/api/client";
import type { SelectCarrierRequest } from "@/lib/api/types";

/** Submits a stored Order again under the current rules; the result is a new Selection. */
export function RerunButton({ input }: { input: SelectCarrierRequest }) {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);

  async function rerun() {
    setPending(true);
    setFailed(false);
    try {
      const { data } = await api.POST("/select-carrier", { body: input });
      if (data?.selection_id != null) {
        router.push(`/selections/${data.selection_id}`);
        return;
      }
      setFailed(true);
    } catch {
      setFailed(true);
    }
    setPending(false);
  }

  return (
    <div className="flex items-center gap-3">
      <Button onClick={rerun} disabled={pending}>
        {pending ? <Loader2 className="animate-spin" aria-hidden /> : <RotateCw aria-hidden />}
        Tekrar çalıştır
      </Button>
      {failed && <span className="text-destructive text-sm">Tekrar çalıştırılamadı.</span>}
    </div>
  );
}
