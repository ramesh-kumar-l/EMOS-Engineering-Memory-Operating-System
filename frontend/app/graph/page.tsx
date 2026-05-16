"use client";

import { useEffect, useCallback, useState } from "react";
import useSWR from "swr";
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import { memoryApi } from "@/lib/api";
import { Share2, Loader2 } from "lucide-react";
import type { Document } from "@/lib/types";

const NODE_WIDTH = 180;
const NODE_HEIGHT = 60;

function buildGraph(docs: Document[]): { nodes: Node[]; edges: Edge[] } {
  const slugSet = new Set(docs.map((d) => d.slug));
  const categoryGroups: Record<string, Document[]> = {};
  docs.forEach((d) => {
    (categoryGroups[d.category] = categoryGroups[d.category] || []).push(d);
  });

  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const edgeSet = new Set<string>();

  const categories = Object.keys(categoryGroups);
  const angleStep = (2 * Math.PI) / Math.max(categories.length, 1);
  const radius = Math.max(200, categories.length * 80);

  categories.forEach((cat, ci) => {
    const angle = ci * angleStep;
    const cx = Math.cos(angle) * radius + radius + 100;
    const cy = Math.sin(angle) * radius + radius + 100;
    const catDocs = categoryGroups[cat];
    const catAngleStep = (2 * Math.PI) / Math.max(catDocs.length, 1);
    const innerR = Math.min(100, catDocs.length * 25 + 40);

    catDocs.forEach((doc, di) => {
      const a = di * catAngleStep;
      nodes.push({
        id: doc.slug,
        data: { label: doc.title, category: doc.category, slug: doc.slug },
        position: {
          x: cx + Math.cos(a) * innerR,
          y: cy + Math.sin(a) * innerR,
        },
        style: {
          background: "#13161f",
          border: "1px solid #1e2433",
          color: "#cbd5e1",
          fontSize: "11px",
          borderRadius: "6px",
          padding: "8px 10px",
          width: NODE_WIDTH,
          minHeight: NODE_HEIGHT,
        },
      });

      doc.tags.forEach((tag) => {
        docs.forEach((other) => {
          if (other.slug !== doc.slug && other.tags.includes(tag) && slugSet.has(other.slug)) {
            const key = [doc.slug, other.slug].sort().join("__");
            if (!edgeSet.has(key)) {
              edgeSet.add(key);
              edges.push({
                id: key,
                source: doc.slug,
                target: other.slug,
                style: { stroke: "#2563eb", strokeWidth: 1, opacity: 0.4 },
                markerEnd: { type: MarkerType.ArrowClosed, color: "#2563eb", width: 10, height: 10 },
              });
            }
          }
        });
      });
    });
  });

  return { nodes, edges };
}

export default function GraphPage() {
  const { data, isLoading } = useSWR("/memory?graph", () => memoryApi.list({ limit: 500 }));
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selected, setSelected] = useState<Document | null>(null);

  useEffect(() => {
    if (data?.documents) {
      const { nodes: n, edges: e } = buildGraph(data.documents);
      setNodes(n);
      setEdges(e);
    }
  }, [data, setNodes, setEdges]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    const doc = data?.documents.find((d) => d.slug === node.id);
    setSelected(doc ?? null);
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        <Loader2 size={18} className="animate-spin mr-2" /> Building graph…
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-6 py-4 border-b border-[#1e2433] flex items-center gap-2">
        <Share2 size={16} className="text-blue-400" />
        <span className="text-sm font-bold text-slate-200">Memory Graph</span>
        <span className="text-xs text-slate-500 ml-2">{data?.total ?? 0} documents · edges = shared tags</span>
      </div>
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          attributionPosition="bottom-right"
          style={{ background: "#0f1117" }}
        >
          <Background variant={BackgroundVariant.Dots} color="#1e2433" gap={20} />
          <Controls style={{ background: "#13161f", border: "1px solid #1e2433" }} />
          <MiniMap
            style={{ background: "#13161f", border: "1px solid #1e2433" }}
            nodeColor="#2563eb"
            maskColor="rgba(0,0,0,0.5)"
          />
        </ReactFlow>

        {selected && (
          <div className="absolute top-4 right-4 w-72 bg-[#13161f] border border-[#1e2433] rounded-lg p-4 shadow-lg z-10">
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-200 truncate">{selected.title}</p>
                <p className="text-xs text-slate-500 font-mono">{selected.slug}</p>
              </div>
              <button onClick={() => setSelected(null)} className="text-slate-600 hover:text-slate-400 text-lg leading-none">×</button>
            </div>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">{selected.category}</span>
            {selected.tags.length > 0 && (
              <div className="flex gap-1 flex-wrap mt-2">
                {selected.tags.map((t) => (
                  <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-900/30 text-blue-400">{t}</span>
                ))}
              </div>
            )}
            <p className="text-xs text-slate-500 mt-3 line-clamp-4">{selected.content}</p>
            <a
              href={`/memory/${selected.slug}`}
              className="block mt-3 text-xs text-blue-400 hover:underline"
            >
              Open document →
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
