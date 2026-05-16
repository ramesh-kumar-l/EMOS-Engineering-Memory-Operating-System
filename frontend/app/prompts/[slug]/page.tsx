"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR, { mutate } from "swr";
import { promptsApi } from "@/lib/api";
import { ArrowLeft, Save, Trash2, Loader2, Play, History } from "lucide-react";
import Link from "next/link";
import { formatDate } from "@/lib/utils";

export default function PromptDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const isNew = slug === "new";

  const { data: template } = useSWR(isNew ? null : `/prompts/${slug}`, () => promptsApi.get(slug));
  const { data: usageData } = useSWR(isNew ? null : `/prompts/${slug}/usage`, () => promptsApi.getUsage(slug, 20));

  const [editing, setEditing] = useState(isNew);
  const [newSlug, setNewSlug] = useState("");
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [content, setContent] = useState("");
  const [saving, setSaving] = useState(false);

  const [renderParams, setRenderParams] = useState<Record<string, string>>({});
  const [rendered, setRendered] = useState<string | null>(null);
  const [rendering, setRendering] = useState(false);
  const [showUsage, setShowUsage] = useState(false);

  useEffect(() => {
    if (template) {
      setTitle(template.title);
      setCategory(template.category);
      setContent(template.content);
      const params: Record<string, string> = {};
      template.parameters.forEach((p) => { params[p] = ""; });
      setRenderParams(params);
    }
  }, [template]);

  async function handleSave() {
    setSaving(true);
    try {
      if (isNew) {
        await promptsApi.create({ slug: newSlug.trim(), title, category, content });
        mutate(`/prompts?cat=`);
        router.push(`/prompts/${newSlug.trim()}`);
      } else {
        await promptsApi.update(slug, { title, category, content });
        mutate(`/prompts/${slug}`);
        mutate(`/prompts?cat=`);
        setEditing(false);
      }
    } catch (e) {
      alert(`Save failed: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${template?.title}"?`)) return;
    await promptsApi.delete(slug);
    mutate(`/prompts?cat=`);
    router.push("/prompts");
  }

  async function handleRender() {
    setRendering(true);
    try {
      const r = await promptsApi.render(slug, { parameters: renderParams });
      setRendered(r.rendered);
    } catch (e) {
      alert(`Render failed: ${(e as Error).message}`);
    } finally {
      setRendering(false);
    }
  }

  const params = template?.parameters ?? [];

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/prompts" className="text-slate-500 hover:text-slate-300 transition-colors">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="flex gap-2">
              {isNew && (
                <input
                  value={newSlug}
                  onChange={(e) => setNewSlug(e.target.value)}
                  placeholder="slug"
                  className="w-36 bg-[#1e2433] border border-[#2a3347] rounded px-2 py-1 text-xs text-slate-300 font-mono focus:outline-none focus:border-blue-600/50"
                />
              )}
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Template title"
                className="flex-1 bg-[#1e2433] border border-[#2a3347] rounded px-3 py-1 text-base font-semibold text-slate-100 focus:outline-none focus:border-blue-600/50"
              />
            </div>
          ) : (
            <div>
              <h1 className="text-xl font-bold text-slate-100">{template?.title}</h1>
              <span className="text-xs text-slate-500 font-mono">{slug} · v{template?.version}</span>
            </div>
          )}
        </div>
        <div className="flex gap-2 shrink-0">
          {!isNew && !editing && (
            <>
              <button
                onClick={() => setShowUsage(!showUsage)}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors"
              >
                <History size={12} /> Usage
              </button>
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors"
              >
                Edit
              </button>
              <button
                onClick={handleDelete}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-red-900/30 border border-red-900/50 text-red-400 hover:bg-red-900/50 transition-colors"
              >
                <Trash2 size={12} /> Delete
              </button>
            </>
          )}
          {editing && (
            <>
              {!isNew && (
                <button onClick={() => setEditing(false)} className="text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors">
                  Cancel
                </button>
              )}
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
              >
                {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                Save
              </button>
            </>
          )}
        </div>
      </div>

      {editing ? (
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-xs text-slate-500 mb-1 block">Category</label>
              <input value={category} onChange={(e) => setCategory(e.target.value)} className="w-full bg-[#13161f] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600/50" />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Template Content (use {"{{param}}"} for parameters)</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={16}
              className="w-full bg-[#13161f] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-blue-600/50 resize-y"
            />
          </div>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
            <p className="text-xs text-slate-500 mb-2">Template</p>
            <pre className="text-sm text-slate-300 font-mono whitespace-pre-wrap">{template?.content}</pre>
          </div>

          {params.length > 0 && (
            <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
              <p className="text-xs text-slate-500 mb-3">Render Preview</p>
              <div className="grid grid-cols-2 gap-2 mb-3">
                {params.map((p) => (
                  <div key={p}>
                    <label className="text-xs text-slate-500 mb-1 block font-mono">{"{" + p + "}"}</label>
                    <input
                      value={renderParams[p] ?? ""}
                      onChange={(e) => setRenderParams({ ...renderParams, [p]: e.target.value })}
                      className="w-full bg-[#0f1117] border border-[#1e2433] rounded px-2 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-blue-600/50"
                    />
                  </div>
                ))}
              </div>
              <button
                onClick={handleRender}
                disabled={rendering}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-green-700 text-white hover:bg-green-600 disabled:opacity-50 transition-colors"
              >
                {rendering ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} />}
                Render
              </button>
              {rendered && (
                <pre className="mt-3 p-3 bg-[#0f1117] border border-[#1e2433] rounded text-sm text-slate-300 font-mono whitespace-pre-wrap">
                  {rendered}
                </pre>
              )}
            </div>
          )}

          {showUsage && (
            <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
              <p className="text-xs text-slate-500 mb-3">Usage History ({usageData?.total ?? 0} records)</p>
              {(usageData?.records.length ?? 0) === 0 ? (
                <p className="text-xs text-slate-600">No usage records yet.</p>
              ) : (
                <div className="space-y-2">
                  {usageData?.records.map((r) => (
                    <div key={r.id} className="text-xs p-2 bg-[#0f1117] border border-[#1e2433] rounded font-mono">
                      <span className="text-slate-500">{formatDate(r.created_at)}</span>
                      {r.outcome && <span className="ml-3 text-green-400">{r.outcome}</span>}
                      {r.tokens_input != null && (
                        <span className="ml-3 text-slate-500">{r.tokens_input}in / {r.tokens_output}out tok</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
