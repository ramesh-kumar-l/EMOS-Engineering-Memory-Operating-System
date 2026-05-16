"use client";

import { useState } from "react";
import useSWR, { mutate } from "swr";
import Link from "next/link";
import { memoryApi } from "@/lib/api";
import { formatDate, truncate } from "@/lib/utils";
import { Search, Plus, RefreshCw, Tag, Loader2, BookOpen } from "lucide-react";
import type { Document } from "@/lib/types";

function DocCard({ doc }: { doc: Document }) {
  return (
    <Link
      href={`/memory/${doc.slug}`}
      className="group block bg-[#13161f] border border-[#1e2433] rounded-lg p-4 hover:border-blue-600/40 hover:bg-blue-600/5 transition-all"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-200 group-hover:text-blue-300 truncate">
            {doc.title}
          </p>
          <p className="text-xs text-slate-500 mt-0.5 font-mono">{doc.slug}</p>
        </div>
        <span className="shrink-0 text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
          {doc.category}
        </span>
      </div>
      <p className="text-xs text-slate-500 mt-2 line-clamp-2">{truncate(doc.content, 120)}</p>
      <div className="flex items-center justify-between mt-3">
        {doc.tags.length > 0 && (
          <div className="flex gap-1 flex-wrap">
            {doc.tags.slice(0, 3).map((t) => (
              <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">
                {t}
              </span>
            ))}
          </div>
        )}
        <span className="text-[10px] text-slate-600 ml-auto">{formatDate(doc.updated_at)}</span>
      </div>
    </Link>
  );
}

export default function MemoryPage() {
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [syncing, setSyncing] = useState(false);

  const searchKey = q.trim() ? `/memory/search?q=${q}` : null;
  const listKey = `/memory?cat=${category}`;

  const { data: searchResults, isLoading: searching } = useSWR(
    searchKey,
    () => memoryApi.search(q.trim())
  );
  const { data: listData, isLoading: listing } = useSWR(
    listKey,
    () => memoryApi.list({ category: category || undefined, limit: 100 })
  );

  const docs: Document[] = q.trim()
    ? (searchResults?.documents ?? [])
    : (listData?.documents ?? []);

  const total = q.trim() ? searchResults?.total : listData?.total;
  const loading = q.trim() ? searching : listing;

  async function handleSync() {
    setSyncing(true);
    try {
      const r = await memoryApi.sync();
      alert(`Synced ${r.synced} documents, skipped ${r.skipped}.`);
      mutate(listKey);
    } catch (e) {
      alert(`Sync failed: ${(e as Error).message}`);
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <BookOpen size={18} className="text-blue-400" />
            Memory Bank
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {total != null ? `${total} document${total !== 1 ? "s" : ""}` : "Loading…"}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 disabled:opacity-50 transition-colors"
          >
            <RefreshCw size={12} className={syncing ? "animate-spin" : ""} />
            Sync
          </button>
          <Link
            href="/memory/new"
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors"
          >
            <Plus size={12} />
            New
          </Link>
        </div>
      </div>

      <div className="flex gap-3 mb-5">
        <div className="relative flex-1">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search documents…"
            className="w-full bg-[#13161f] border border-[#1e2433] rounded-lg pl-8 pr-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-600/50"
          />
        </div>
        <div className="relative">
          <Tag size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="Category"
            className="w-36 bg-[#13161f] border border-[#1e2433] rounded-lg pl-8 pr-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-600/50"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-16 text-slate-500">
          <Loader2 size={18} className="animate-spin mr-2" />
          Loading…
        </div>
      ) : docs.length === 0 ? (
        <div className="text-center py-16 text-slate-500 text-sm">
          No documents found.{" "}
          {!q && (
            <button onClick={handleSync} className="text-blue-400 hover:underline">
              Sync from disk
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {docs.map((d) => (
            <DocCard key={d.slug} doc={d} />
          ))}
        </div>
      )}
    </div>
  );
}
