import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { AppSidebar } from "@/components/app-sidebar";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

// latin-ext covers Turkish characters (ş, ğ, ı, İ).
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
});

export const metadata: Metadata = {
  title: "Carrier Selector",
  description: "Konteyner siparişleri için taşıyıcı seçim paneli",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="tr" className={`${inter.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col md:flex-row">
        <AppSidebar />
        <main className="min-w-0 flex-1 px-4 py-6 md:px-8 md:py-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
        <Toaster />
      </body>
    </html>
  );
}
