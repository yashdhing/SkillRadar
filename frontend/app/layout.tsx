import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkillRadar",
  description: "Generate grounded study lessons for backend and systems growth.",
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

