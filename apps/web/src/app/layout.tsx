import type { Metadata } from "next";
import { connection } from "next/server";
import "./globals.css";
export const metadata: Metadata = {
  title: "AI Company OS · Mission Control",
  description: "Your autonomous venture studio. Real work, visible.",
};
export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // The request-scoped CSP nonce is injected by proxy.ts. Rendering this shell
  // per request lets Next attach that nonce to its framework and RSC scripts.
  await connection();
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
