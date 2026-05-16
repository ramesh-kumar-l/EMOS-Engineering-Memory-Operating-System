"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BookOpen,
  Search,
  Layers,
  FileText,
  GitBranch,
  FolderCode,
  Share2,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: Activity },
  { href: "/memory", label: "Memory Bank", icon: BookOpen },
  { href: "/search", label: "Search", icon: Search },
  { href: "/context", label: "Context", icon: Layers },
  { href: "/prompts", label: "Prompts", icon: FileText },
  { href: "/workflows", label: "Workflows", icon: GitBranch },
  { href: "/repo", label: "Repo Intel", icon: FolderCode },
  { href: "/graph", label: "Graph", icon: Share2 },
];

export function NavSidebar() {
  const path = usePathname();
  return (
    <aside className="w-[220px] shrink-0 flex flex-col bg-[#13161f] border-r border-[#1e2433] h-full">
      <div className="px-4 py-5 border-b border-[#1e2433]">
        <span className="text-sm font-bold tracking-widest text-blue-400 uppercase">EMOS</span>
        <p className="text-[10px] text-slate-500 mt-0.5">Engineering Memory OS</p>
      </div>
      <nav className="flex-1 px-2 py-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? path === "/" : path.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded text-sm transition-colors",
                active
                  ? "bg-blue-600/20 text-blue-400"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              <Icon size={15} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="px-4 py-3 border-t border-[#1e2433] text-[10px] text-slate-600">
        v0.1.0 · offline-first
      </div>
    </aside>
  );
}
