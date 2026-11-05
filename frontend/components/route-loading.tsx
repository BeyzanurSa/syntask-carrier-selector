import { Loader2 } from "lucide-react";

export function RouteLoading() {
  return (
    <p className="text-muted-foreground flex items-center gap-2 text-sm" role="status">
      <Loader2 className="size-4 animate-spin" aria-hidden />
      Yükleniyor…
    </p>
  );
}
