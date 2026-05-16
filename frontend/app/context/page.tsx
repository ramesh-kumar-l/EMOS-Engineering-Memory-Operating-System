"use client";

import { useState } from "react";
import { contextApi } from "@/lib/api";
import { Layers, Loader2, Zap, Copy } from "lucide-react";
import type { ContextChunk } from "@/lib/types";

function ChunkCard({ chunk, index }: { chunk: ContextChunk; index: number }) {
  return (
    <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <span className="text-[10px] text-slate-600 font-mono mr-2">#{index + 1}</span>
          <span className="text-sm font-medium text-slate-200">{chunk.title}</span>
          <span className="ml-2 text-xs text-slate-500 font-mono">{chunk.slug}</span>
        </div>
        <div className="flex items-center gap-2 shrink-0 text-[10px] font-mono">
          <span className="px-1.5 py-0.5 rounded bg-green-900/30 text-green-400">{(chunk.score * 100).toFixed(0)}%</span>
          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-500">{chunk.tokens} tok</span>
        </div>
      </div>
      <pre className="text-xs text-slate-500 font-mono whitespace-pre-wrap line-clamp-4">{chunk.content}</pre>
    </div>
  );
}

export default function ContextPage() {
  const [query, setQuery] = useState("");
  const [budget, setBudget] = useState(80000);
  const [alpha, setAlpha] = useState(0.5);
  const [result, setResult] = useState<{
    query: string;
    chunks: ContextChunk[];
    total_tokens: number;
    budget: number;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAssemble(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const r = await contextApi.assemble({ query: query.trim(), token_budget: budget, alpha });
      setResult(r);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  function copyContext() {
    if (!result) return;
    const text = result.chunks.map((c) => `# ${c.title}\n${c.content}`).join("\n\n---\n\n");
    navigator.clipboard.writeText(text);
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <Layers size={18} className="text-blue-400" />
          Context Assembly
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">Build token-efficient context packages for AI sessions</p>
      </div>

      <form onSubmit={handleAssemble} className="bg-[#13161f] border border-[#1e2433] rounded-lg p-5 mb-5">
        <div className="mb-4">
          <label className="text-xs text-slate-400 mb-1.5 block">Query / Task Description</label>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
            placeholder="Describe what you're working on or ask a question…"
            className="w-full bg-[#0f1117] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-600/50 resize-none"
          />
        </div>
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <label className="text-xs text-slate-400 mb-1.5 block">Token Budget: {budget.toLocaleString()}</label>
            <input
              type="range"
              min={1000}
              max={200000}
              step={1000}
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-slate-600 mt-1">
              <span>1K</span><span>200K</span>
            </div>
          </div>
          <div className="w-40">
            <label className="text-xs text-slate-400 mb-1.5 block">Semantic Weight (α): {alpha}</label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={alpha}
              onChange={(e) => setAlpha(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-slate-600 mt-1">
              <span>keyword</span><span>semantic</span>
            </div>
          </div>
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="flex items-center gap-2 px-4 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Zap size={14} />}
          Assemble Context
        </button>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg text-sm text-red-400">
          {error}
        </div>
      )}

      {result && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="text-xs text-slate-400">
              <span className="text-slate-200 font-medium">{result.chunks.length}</span> chunks ·{" "}
              <span className="text-slate-200 font-medium">{result.total_tokens.toLocaleString()}</span> /{" "}
              {result.budget.toLocaleString()} tokens used
            </div>
            <button
              onClick={copyContext}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors"
            >
              <Copy size={11} /> Copy Context
            </button>
          </div>
          <div className="mb-3 bg-[#13161f] border border-[#1e2433] rounded-lg p-3">
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>Token usage</span>
              <span>{((result.total_tokens / result.budget) * 100).toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 rounded-full transition-all"
                style={{ width: `${Math.min(100, (result.total_tokens / result.budget) * 100)}%` }}
              />
            </div>
          </div>
          <div className="space-y-3">
            {result.chunks.map((chunk, i) => (
              <ChunkCard key={chunk.slug} chunk={chunk} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
