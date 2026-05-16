"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR, { mutate } from "swr";
import { memoryApi } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { ArrowLeft, Save, Trash2, Loader2, Edit3 } from "lucide-react";
import Link from "next/link";

export default function DocumentPage() {
  const { slug } = useParams<{ slug: string }>();
  const router = useRouter();
  const isNew = slug === "new";

  const { data: doc, isLoading } = useSWR(
    isNew ? null : `/memory/${slug}`,
    () => memoryApi.get(slug)
  );

  const [editing, setEditing] = useState(isNew);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (doc) {
      setTitle(doc.title);
      setCategory(doc.category);
      setContent(doc.content);
      setTags(doc.tags.join(", "));
    }
  }, [doc]);

  async function handleSave() {
    setSaving(true);
    try {
      if (isNew) {
        await memoryApi.create({
          slug: newSlug.trim(),
          title,
          category,
          content,
          tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        });
        mutate("/memory?cat=");
        router.push(`/memory/${newSlug.trim()}`);
      } else {
        await memoryApi.update(slug, {
          title,
          category,
          content,
          tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        });
        mutate(`/memory/${slug}`);
        mutate("/memory?cat=");
        setEditing(false);
      }
    } catch (e) {
      alert(`Save failed: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete "${doc?.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await memoryApi.delete(slug);
      mutate("/memory?cat=");
      router.push("/memory");
    } catch (e) {
      alert(`Delete failed: ${(e as Error).message}`);
      setDeleting(false);
    }
  }

  if (!isNew && isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-slate-500">
        <Loader2 size={18} className="animate-spin mr-2" /> Loading…
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/memory" className="text-slate-500 hover:text-slate-300 transition-colors">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1 min-w-0">
          {editing ? (
            <div className="flex gap-2">
              {isNew && (
                <input
                  value={newSlug}
                  onChange={(e) => setNewSlug(e.target.value)}
                  placeholder="slug (e.g. my-document)"
                  className="w-40 bg-[#1e2433] border border-[#2a3347] rounded px-2 py-1 text-xs text-slate-300 font-mono focus:outline-none focus:border-blue-600/50"
                />
              )}
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Document title"
                className="flex-1 bg-[#1e2433] border border-[#2a3347] rounded px-3 py-1 text-base font-semibold text-slate-100 focus:outline-none focus:border-blue-600/50"
              />
            </div>
          ) : (
            <h1 className="text-xl font-bold text-slate-100 truncate">{doc?.title}</h1>
          )}
        </div>
        <div className="flex gap-2 shrink-0">
          {!isNew && !editing && (
            <>
              <button
                onClick={() => setEditing(true)}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-300 hover:text-slate-100 transition-colors"
              >
                <Edit3 size={12} /> Edit
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded bg-red-900/30 border border-red-900/50 text-red-400 hover:bg-red-900/50 disabled:opacity-50 transition-colors"
              >
                {deleting ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                Delete
              </button>
            </>
          )}
          {editing && (
            <>
              {!isNew && (
                <button
                  onClick={() => { setEditing(false); }}
                  className="text-xs px-3 py-1.5 rounded bg-slate-800 border border-slate-700 text-slate-400 hover:text-slate-200 transition-colors"
                >
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
              <input
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                placeholder="e.g. architecture, decisions"
                className="w-full bg-[#13161f] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600/50"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-slate-500 mb-1 block">Tags (comma-separated)</label>
              <input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g. api, backend, auth"
                className="w-full bg-[#13161f] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600/50"
              />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-500 mb-1 block">Content (Markdown)</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={24}
              className="w-full bg-[#13161f] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 font-mono focus:outline-none focus:border-blue-600/50 resize-y"
            />
          </div>
        </div>
      ) : (
        <div>
          <div className="flex items-center gap-4 mb-4 text-xs text-slate-500">
            <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
              {doc?.category}
            </span>
            {doc?.tags.map((t) => (
              <span key={t} className="px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">
                {t}
              </span>
            ))}
            <span className="ml-auto">Updated {doc && formatDate(doc.updated_at)}</span>
          </div>
          <pre className="bg-[#13161f] border border-[#1e2433] rounded-lg p-5 text-sm text-slate-300 font-mono whitespace-pre-wrap leading-relaxed overflow-x-auto">
            {doc?.content}
          </pre>
        </div>
      )}
    </div>
  );
}
