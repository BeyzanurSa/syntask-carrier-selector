import { BackendStatus } from "@/components/backend-status";
import { PageHeader } from "@/components/page-header";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Taşıyıcı ağı ve son seçimlerin özeti"
      />
      <Card className="max-w-md">
        <CardHeader>
          <CardTitle>Sistem durumu</CardTitle>
          <CardDescription>Backend bağlantısı</CardDescription>
        </CardHeader>
        <CardContent>
          <BackendStatus />
        </CardContent>
      </Card>
    </>
  );
}
