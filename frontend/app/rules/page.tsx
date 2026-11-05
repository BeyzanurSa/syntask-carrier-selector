import type { Metadata } from "next";

import { PageHeader } from "@/components/page-header";
import { RulesEditor } from "@/components/rules/rules-editor";
import { fetchRules } from "@/lib/api/server";

export const metadata: Metadata = { title: "Kurallar · Carrier Selector" };

export default async function RulesPage() {
  const rules = await fetchRules();

  return (
    <>
      <PageHeader title="Kurallar" description="Sıralama kriterlerinin önceliğini yönetin" />
      <RulesEditor rules={rules} />
    </>
  );
}
