"use client";

import Link from "next/link";
import useSWR from "swr";
import { memoryApi, retrievalApi, workflowsApi } from "@/lib/api";
import { BookOpen, Search, GitBranch, FileText, FolderCode, Layers, RefreshCw } from "lucide-react";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
      <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}

const QUICK_LINKS = [
  { href: "/memory", icon: BookOpen, label: "Browse Memory", desc: "View and edit documents" },
  { href: "/search", icon: Search, label: "Search", desc: "Semantic + keyword search" },
  { href: "/context", icon: Layers, label: "Assemble Context", desc: "Build AI context packages" },
  { href: "/prompts", icon: FileText, label: "Prompts", desc: "Manage prompt templates" },
  { href: "/workflows", icon: GitBranch, label: "Workflows", desc: "Run engineering workflows" },
  { href: "/repo", icon: FolderCode, label: "Repo Intel", desc: "Analyze repository structure" },
];

export default function Dashboard() {
  const { data: memList } = useSWR("/memory", () => memoryApi.list({ limit: 1 }));
  const { data: indexStatus } = useSWR("/retrieval/status", retrievalApi.status);
  const { data: runs } = useSWR("/workflows/runs", () => workflowsApi.listRuns({ status: "running" }));

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Engineering Memory Operating System — offline-first</p>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard
          label="Memory Documents"
          value={memList?.total ?? "—"}
          sub="in memory bank"
        />
        <StatCard
          label="Vector Index"
          value={indexStatus?.ready ? `${indexStatus.indexed} indexed` : "Not built"}
          sub={indexStatus?.ready ? "ready for semantic search" : "run /retrieval/index to build"}
        />
        <StatCard
          label="Active Workflows"
          value={runs?.total ?? "—"}
          sub="runs in progress"
        />
      </div>

      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Quick Access</h2>
      <div className="grid grid-cols-3 gap-3">
        {QUICK_LINKS.map(({ href, icon: Icon, label, desc }) => (
          <Link
            key={href}
            href={href}
            className="group bg-[#13161f] border border-[#1e2433] rounded-lg p-4 hover:border-blue-600/50 hover:bg-blue-600/5 transition-all"
          >
            <Icon size={18} className="text-blue-400 mb-2" />
            <p className="text-sm font-medium text-slate-200 group-hover:text-blue-300">{label}</p>
            <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
          </Link>
        ))}
      </div>

      <div className="mt-8 p-4 bg-[#13161f] border border-[#1e2433] rounded-lg">
        <div className="flex items-center gap-2 mb-2">
          <RefreshCw size={14} className="text-slate-400" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Backend</span>
        </div>
        <p className="text-xs text-slate-500">
          API: <code className="text-green-400">http://localhost:8000</code> ·{" "}
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline">
            OpenAPI Docs
          </a>
        </p>
      </div>
    </div>
  );
}
