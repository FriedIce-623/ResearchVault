import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ResearchVault",
  description: "AI-powered research paper analyser",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
