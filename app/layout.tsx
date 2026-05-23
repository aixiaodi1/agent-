import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LangGraph Trace Workbench",
  description: "Debug FastAPI and LangGraph agent runs from a focused Next.js console."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
