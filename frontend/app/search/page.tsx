"use client";

import { useState } from "react";
import Link from "next/link";
import { retrievalApi } from "@/lib/api";
import { Search, Loader2, Zap, Database, RefreshCw } from "lucide-react";
import type { SearchHit } from "@/lib/types";
import useSWR from "swr";

function HitCard({ hit }: { hit: SearchHit }) {
  return (
    <Link
      href={`/memory/${hit.slug}`}
      className="group block bg-[#13161f] border border-[#1e2433] rounded-lg p-4 hover:border-blue-600/40 hover:bg-blue-600/5 transition-all"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-200 group-hover:text-blue-300 truncate">
            {hit.title}
          </p>
          <p className="text-xs text-slate-500 font-mono">{hit.slug}</p>
        </div>
        <span className="shrink-0 text-[10px] font-mono px-2 py-0.5 rounded bg-green-900/30 text-green-400 border border-green-900/50">
          {(hit.score * 100).toFixed(0)}%
        </span>
      </div>
      {hit.snippet && (
        <p className="text-xs text-slate-500 mt-2 line-clamp-2">{hit.snippet}</p>
      )}
      <p className="text-[10px] text-slate-600 mt-2">{hit.category}</p>
    </Link>
  );
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"hybrid" | "semantic" | "keyword">("hybrid");
  const [results, setResults] = useState<SearchHit[] | null>(null);
  const [total, setTotal] = useState<number>(0);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [building, setBuilding] = useState(false);

  const { data: status, mutate: refetchStatus } = useSWR("/retrieval/status", retrievalApi.status);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const r = await retrievalApi.search({ q: query.trim(), mode, limit: 20 });
      setResults(r.hits);
      setTotal(r.total);
    } catch (e) {
      setError((e as Error).message);
      setResults(null);
    } finally {
      setSearching(false);
    }
  }

  async function handleBuildIndex() {
    setBuilding(true);
    try {
      await retrievalApi.buildIndex();
      await refetchStatus();
      alert("Index built successfully.");
    } catch (e) {
      alert(`Build failed: ${(e as Error).message}`);
    } finally {
      setBuilding(false);
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Search size={18} className="text-blue-400" />
          Search
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">Semantic, keyword, or hybrid search across memory bank</p>
      </div>

      <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4 mb-5 flex items-center gap-4">
        <Database size={14} className="text-slate-400" />
        <div className="text-xs text-slate-400">
          Index: {status?.ready
            ? <span className="text-green-400">{status.indexed} documents indexed</span>
            : <span className="text-yellow-400">not built</span>}
        </div>
        <button
          onClick={handleBuildIndex}
          disabled={building}
          className="ml-auto flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 disabled:opacity-50 transition-colors"
        >
          <RefreshCw size={11} className={building ? "animate-spin" : ""} />
          {status?.ready ? "Rebuild Index" : "Build Index"}
        </button>
      </div>

      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-2 mb-2">
          <div className="relative flex-1">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search your memory bank…"
              className="w-full bg-[#13161f] border border-[#1e2433] rounded-lg pl-8 pr-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-600/50"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !query.trim()}
            className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors"
          >
            {searching ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
            Search
          </button>
        </div>
        <div className="flex gap-2">
          {(["hybrid", "semantic", "keyword"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                mode === m
                  ? "bg-blue-600/20 border-blue-600/50 text-blue-400"
                  : "bg-transparent border-[#1e2433] text-slate-500 hover:text-slate-300"
              }`}
            >
              {m}
            </button>
          ))}
        </div>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {results !== null && (
        <div>
          <p className="text-xs text-slate-500 mb-3">
            {total} result{total !== 1 ? "s" : ""} for "<span className="text-slate-300">{query}</span>" · mode: {mode}
          </p>
          {results.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">No results found.</div>
          ) : (
            <div className="space-y-3">
              {results.map((hit) => (
                <HitCard key={hit.slug} hit={hit} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
