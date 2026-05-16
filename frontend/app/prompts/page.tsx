"use client";

import { useState } from "react";
import useSWR from "swr";
import Link from "next/link";
import { promptsApi } from "@/lib/api";
import { FileText, Plus, Loader2 } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { PromptTemplate } from "@/lib/types";

function TemplateCard({ t }: { t: PromptTemplate }) {
  return (
    <Link
      href={`/prompts/${t.slug}`}
      className="group block bg-[#13161f] border border-[#1e2433] rounded-lg p-4 hover:border-blue-600/40 hover:bg-blue-600/5 transition-all"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-200 group-hover:text-blue-300 truncate">{t.title}</p>
          <p className="text-xs text-slate-500 font-mono">{t.slug}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">v{t.version}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">{t.category}</span>
        </div>
      </div>
      {t.parameters.length > 0 && (
        <div className="flex gap-1 mt-2 flex-wrap">
          {t.parameters.map((p) => (
            <span key={p} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400 font-mono">
              {"{" + p + "}"}
            </span>
          ))}
        </div>
      )}
      <p className="text-[10px] text-slate-600 mt-2">{formatDate(t.updated_at)}</p>
    </Link>
  );
}

export default function PromptsPage() {
  const [category, setCategory] = useState("");
  const { data, isLoading } = useSWR(
    `/prompts?cat=${category}`,
    () => promptsApi.list(category || undefined)
  );

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <FileText size={18} className="text-blue-400" />
            Prompt Registry
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {data?.total != null ? `${data.total} template${data.total !== 1 ? "s" : ""}` : "Loading…"}
          </p>
        </div>
        <Link
          href="/prompts/new"
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors"
        >
          <Plus size={12} /> New Template
        </Link>
      </div>

      <div className="mb-4">
        <input
          type="text"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          placeholder="Filter by category…"
          className="w-60 bg-[#13161f] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-600/50"
        />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-16 text-slate-500">
          <Loader2 size={18} className="animate-spin mr-2" /> Loading…
        </div>
      ) : (data?.templates.length ?? 0) === 0 ? (
        <div className="text-center py-16 text-slate-500 text-sm">
          No prompt templates yet.{" "}
          <Link href="/prompts/new" className="text-blue-400 hover:underline">Create one</Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {data?.templates.map((t) => <TemplateCard key={t.slug} t={t} />)}
        </div>
      )}
    </div>
  );
}
