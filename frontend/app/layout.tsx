import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RumahAsri — Platform Properti Cerdas",
  description:
    "Solusi manajemen properti terpercaya untuk pengembang perumahan Jambi & Indonesia. Lacak progres konstruksi, kelola penjualan, dan layani pembeli dalam satu platform.",
  keywords: "properti, perumahan, developer, konstruksi, Jambi, Indonesia",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}
