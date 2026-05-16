"use client";

import { useState } from "react";
import useSWR, { mutate } from "swr";
import Link from "next/link";
import { workflowsApi } from "@/lib/api";
import { GitBranch, Play, Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import { formatDate } from "@/lib/utils";
import type { WorkflowDef, WorkflowRun } from "@/lib/types";

function StatusBadge({ status }: { status: WorkflowRun["status"] }) {
  const map = {
    running: { icon: Clock, cls: "text-yellow-400 bg-yellow-900/20 border-yellow-900/40" },
    completed: { icon: CheckCircle2, cls: "text-green-400 bg-green-900/20 border-green-900/40" },
    cancelled: { icon: XCircle, cls: "text-slate-400 bg-slate-800 border-slate-700" },
  };
  const { icon: Icon, cls } = map[status];
  return (
    <span className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded border ${cls}`}>
      <Icon size={10} />
      {status}
    </span>
  );
}

function DefCard({ def, onStart }: { def: WorkflowDef; onStart: (id: string) => void }) {
  return (
    <div className="bg-[#13161f] border border-[#1e2433] rounded-lg p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <p className="text-sm font-medium text-slate-200">{def.name}</p>
          <p className="text-xs text-slate-500 font-mono">{def.id}</p>
        </div>
        <button
          onClick={() => onStart(def.id)}
          className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded bg-blue-600 text-white hover:bg-blue-500 transition-colors shrink-0"
        >
          <Play size={11} /> Start
        </button>
      </div>
      <p className="text-xs text-slate-500 mb-3">{def.description}</p>
      <div className="flex gap-1.5 flex-wrap">
        {def.steps.map((s, i) => (
          <span key={s.id} className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
            {i + 1}. {s.name}
          </span>
        ))}
      </div>
    </div>
  );
}

function RunCard({ run }: { run: WorkflowRun }) {
  const step = run.steps[run.current_step];
  const progress = ((run.current_step) / run.steps.length) * 100;
  return (
    <Link
      href={`/workflows/runs/${run.id}`}
      className="block bg-[#13161f] border border-[#1e2433] rounded-lg p-4 hover:border-blue-600/40 hover:bg-blue-600/5 transition-all"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-200 truncate">{run.workflow_name}</p>
          <p className="text-xs text-slate-500 font-mono truncate">{run.id}</p>
        </div>
        <StatusBadge status={run.status} />
      </div>
      {run.status === "running" && step && (
        <p className="text-xs text-slate-400 mb-2">
          Step {run.current_step + 1}/{run.steps.length}: {step.name}
        </p>
      )}
      <div className="h-1 bg-slate-800 rounded-full overflow-hidden mb-2">
        <div
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${run.status === "completed" ? 100 : progress}%` }}
        />
      </div>
      <p className="text-[10px] text-slate-600">{formatDate(run.updated_at)}</p>
    </Link>
  );
}

export default function WorkflowsPage() {
  const { data: defsData } = useSWR("/workflows/definitions", workflowsApi.listDefinitions);
  const { data: runsData } = useSWR("/workflows/runs", () => workflowsApi.listRuns());
  const [starting, setStarting] = useState(false);

  async function handleStart(workflowId: string) {
    setStarting(true);
    try {
      const run = await workflowsApi.startRun({ workflow_id: workflowId });
      mutate("/workflows/runs");
      window.location.href = `/workflows/runs/${run.id}`;
    } catch (e) {
      alert(`Failed to start: ${(e as Error).message}`);
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-slate-100 flex items-center gap-2">
          <GitBranch size={18} className="text-blue-400" />
          Workflows
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">Human-gated engineering workflow execution</p>
      </div>

      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Definitions</h2>
      {(defsData?.definitions.length ?? 0) === 0 ? (
        <p className="text-sm text-slate-500 mb-6">No workflow definitions found.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3 mb-8">
          {defsData?.definitions.map((d) => (
            <DefCard key={d.id} def={d} onStart={handleStart} />
          ))}
        </div>
      )}

      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
        Runs ({runsData?.total ?? 0})
      </h2>
      {(runsData?.runs.length ?? 0) === 0 ? (
        <p className="text-sm text-slate-500">No workflow runs yet.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {runsData?.runs.map((r) => <RunCard key={r.id} run={r} />)}
        </div>
      )}

      {starting && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <Loader2 size={28} className="animate-spin text-blue-400" />
        </div>
      )}
    </div>
  );
}
