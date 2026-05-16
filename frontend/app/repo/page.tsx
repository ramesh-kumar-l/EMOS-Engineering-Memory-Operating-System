"use client";

import { useState } from "react";
import { repoApi } from "@/lib/api";
import { FolderCode, Loader2, AlertTriangle, FileText, Zap, Copy } from "lucide-react";
import type { AnalyzeResponse, RisksResponse, DocsResponse } from "@/lib/types";

type Tab = "analyze" | "risks" | "docs";

function RiskBadge({ severity }: { severity: "low" | "medium" | "high" }) {
  const cls = {
    low: "text-yellow-400 bg-yellow-900/20 border-yellow-900/40",
    medium: "text-orange-400 bg-orange-900/20 border-orange-900/40",
    high: "text-red-400 bg-red-900/20 border-red-900/40",
  }[severity];
  return <span className={`text-[10px] px-1.5 py-0.5 rounded border ${cls}`}>{severity}</span>;
}

export default function RepoPage() {
  const [path, setPath] = useState("");
  const [tab, setTab] = useState<Tab>("analyze");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [risks, setRisks] = useState<RisksResponse | null>(null);
  const [docs, setDocs] = useState<DocsResponse | null>(null);

  async function handleRun() {
    if (!path.trim()) return;
    setLoading(true);
    setError(null);
    try {
      if (tab === "analyze") {
        const r = await repoApi.analyze(path.trim());
        setAnalysis(r);
      } else if (tab === "risks") {
        const r = await repoApi.risks(path.trim());
        setRisks(r);
      } else {
        const r = await repoApi.docs(path.trim());
        setDocs(r);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <FolderCode size={18} className="text-blue-400" />
          Repo Intelligence
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">Analyze repository structure, detect risks, generate docs</p>
      </div>

      <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-5 mb-5">
        <label className="text-xs text-slate-400 mb-1.5 block">Repository Path (absolute)</label>
        <div className="flex gap-2 mb-4">
          <input
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="e.g. /home/user/my-project or C:\projects\my-app"
            className="flex-1 bg-[#0f1117] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-600 font-mono focus:outline-none focus:border-blue-600/50"
          />
        </div>
        <div className="flex gap-2">
          {(["analyze", "risks", "docs"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`text-xs px-3 py-1.5 rounded border transition-colors ${
                tab === t
                  ? "bg-blue-600/20 border-blue-600/50 text-blue-400"
                  : "bg-transparent border-[#1e2433] text-slate-500 hover:text-slate-300"
              }`}
            >
              {t}
            </button>
          ))}
          <button
            onClick={handleRun}
            disabled={loading || !path.trim()}
            className="ml-auto flex items-center gap-1.5 px-4 py-1.5 rounded bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 size={13} className="animate-spin" /> : <Zap size={13} />}
            Run
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-900/50 rounded-lg text-sm text-red-400">{error}</div>
      )}

      {tab === "analyze" && analysis && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Files", value: analysis.total_files },
              { label: "Symbols", value: analysis.total_symbols },
              { label: "Languages", value: Object.keys(analysis.languages).length },
            ].map(({ label, value }) => (
              <div key={label} className="bg-[#13161f] border border-[#1e2433] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-slate-100">{value}</p>
                <p className="text-xs text-slate-500">{label}</p>
              </div>
            ))}
          </div>
          <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
            <p className="text-xs text-slate-500 mb-3">Languages</p>
            {Object.entries(analysis.languages).map(([lang, count]) => (
              <div key={lang} className="flex items-center gap-2 mb-1.5">
                <span className="text-xs text-slate-400 w-24 truncate">{lang}</span>
                <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(count / analysis.total_files) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
          <div className="bg-[#13161f] border border-[#1e2433] rounded-lg overflow-hidden">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[#1e2433]">
                  {["File", "Language", "Lines", "Functions", "Classes"].map((h) => (
                    <th key={h} className="text-left px-3 py-2 text-slate-500 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {analysis.file_summaries.map((f) => (
                  <tr key={f.path} className="border-b border-[#1e2433]/50 hover:bg-white/2">
                    <td className="px-3 py-2 font-mono text-slate-300 max-w-xs truncate">{f.path}</td>
                    <td className="px-3 py-2 text-slate-500">{f.language}</td>
                    <td className="px-3 py-2 text-slate-400">{f.line_count}</td>
                    <td className="px-3 py-2 text-slate-400">{f.function_count}</td>
                    <td className="px-3 py-2 text-slate-400">{f.class_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "risks" && risks && (
        <div>
          <p className="text-sm text-slate-400 mb-3">
            <span className={`font-bold ${risks.risk_count > 0 ? "text-red-400" : "text-green-400"}`}>
              {risks.risk_count}
            </span>{" "}
            risk{risks.risk_count !== 1 ? "s" : ""} detected
          </p>
          {risks.risk_count === 0 ? (
            <div className="text-center py-12 text-green-400 text-sm">No coupling risks detected.</div>
          ) : (
            <div className="space-y-2">
              {risks.risks.map((r, i) => (
                <div key={i} className="bg-[#13161f] border border-[#1e2433] rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle size={13} className="text-orange-400" />
                    <span className="text-xs font-mono text-slate-400">{r.file}</span>
                    <RiskBadge severity={r.severity} />
                    <span className="text-[10px] text-slate-500 ml-auto font-mono">{r.risk_type}</span>
                  </div>
                  <p className="text-xs text-slate-500 pl-5">{r.detail}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "docs" && docs && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <p className="text-sm text-slate-400">Generated: <span className="text-slate-200">{docs.title}</span></p>
            <button
              onClick={() => navigator.clipboard.writeText(docs.markdown)}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors"
            >
              <Copy size={11} /> Copy Markdown
            </button>
          </div>
          <pre className="bg-[#13161f] border border-[#1e2433] rounded-lg p-5 text-sm text-slate-300 font-mono whitespace-pre-wrap overflow-x-auto max-h-[600px] overflow-y-auto">
            {docs.markdown}
          </pre>
        </div>
      )}
    </div>
  );
}
