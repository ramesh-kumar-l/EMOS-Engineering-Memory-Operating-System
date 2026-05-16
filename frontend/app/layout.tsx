import type { Metadata } from "next";
import "./globals.css";
import { NavSidebar } from "@/components/nav-sidebar";

export const metadata: Metadata = {
  title: "EMOS — Engineering Memory Operating System",
  description: "Offline-first engineering memory and workflow operating system",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <body className="h-full flex overflow-hidden">
        <NavSidebar />
        <main className="flex-1 overflow-y-auto bg-[#0f1117]">
          {children}
        </main>
      </body>
    </html>
  );
}
