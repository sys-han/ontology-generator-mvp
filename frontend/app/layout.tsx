import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ontology Builder",
  description: "Use-case-conditioned ontology induction from raw data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
