import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DropRadar - High Value Domain Monitor",
  description: "Monitor and capture high-value expired domains with SEO metrics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
