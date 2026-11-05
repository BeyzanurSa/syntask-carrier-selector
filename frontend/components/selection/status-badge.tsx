import { Badge } from "@/components/ui/badge";
import type { SelectionStatus } from "@/lib/api/types";
import { STATUS_LABELS } from "@/lib/format";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<SelectionStatus, string> = {
  selected: "bg-success/10 text-success",
  no_carrier: "bg-destructive/10 text-destructive",
  unknown_route: "bg-warning/15 text-foreground",
  invalid_order: "bg-muted text-muted-foreground",
  needs_review: "bg-warning/15 text-foreground",
  jev_unavailable: "bg-destructive/10 text-destructive",
};

export function StatusBadge({ status }: { status: SelectionStatus }) {
  return <Badge className={cn("border-transparent", STATUS_STYLES[status])}>{STATUS_LABELS[status]}</Badge>;
}
