"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR, { mutate } from "swr";
import { workflowsApi } from "@/lib/api";
import { ArrowLeft, CheckCircle2, XCircle, Clock, ChevronRight, Loader2, X } from "lucide-react";
import Link from "next/link";
import { formatDate } from "@/lib/utils";

export default function RunDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: run, isLoading, mutate: refetch } = useSWR(`/workflows/runs/${id}`, () => workflowsApi.getRun(id));

  const [outcome, setOutcome] = useState("");
  const [notes, setNotes] = useState("");
  const [advancing, setAdvancing] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  async function handleAdvance() {
    setAdvancing(true);
    try {
      await workflowsApi.advanceStep(id, { outcome: outcome || undefined, notes: notes || undefined });
      setOutcome("");
      setNotes("");
      await refetch();
      mutate("/workflows/runs");
    } catch (e) {
      alert(`Failed: ${(e as Error).message}`);
    } finally {
      setAdvancing(false);
    }
  }

  async function handleCancel() {
    if (!confirm("Cancel this workflow run?")) return;
    setCancelling(true);
    try {
      await workflowsApi.cancelRun(id);
      await refetch();
      mutate("/workflows/runs");
    } catch (e) {
      alert(`Failed: ${(e as Error).message}`);
    } finally {
      setCancelling(false);
    }
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64 text-slate-500"><Loader2 size={18} className="animate-spin mr-2" /> Loading…</div>;
  }

  if (!run) return null;

  const currentStep = run.steps[run.current_step];
  const isRunning = run.status === "running";

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Link href="/workflows" className="text-slate-500 hover:text-slate-300 transition-colors">
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-slate-100 truncate">{run.workflow_name}</h1>
          <p className="text-xs text-slate-500 font-mono truncate">{run.id}</p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs px-2 py-0.5 rounded border ${
            run.status === "running" ? "text-yellow-400 bg-yellow-900/20 border-yellow-900/40" :
            run.status === "completed" ? "text-green-400 bg-green-900/20 border-green-900/40" :
            "text-slate-400 bg-slate-800 border-slate-700"
          }`}>{run.status}</span>
          {isRunning && (
            <button
              onClick={handleCancel}
              disabled={cancelling}
              className="flex items-center gap-1 text-xs px-2.5 py-1.5 rounded bg-red-900/30 border border-red-900/50 text-red-400 hover:bg-red-900/50 disabled:opacity-50 transition-colors"
            >
              {cancelling ? <Loader2 size={11} className="animate-spin" /> : <X size={11} />}
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
          <span>Progress</span>
          <span>{isRunning ? run.current_step : run.steps.length}/{run.steps.length} steps</span>
        </div>
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all"
            style={{
              width: `${run.status === "completed" ? 100 : (run.current_step / run.steps.length) * 100}%`
            }}
          />
        </div>
      </div>

      <div className="space-y-2 mb-6">
        {run.steps.map((step, i) => {
          const done = i < run.current_step || run.status === "completed";
          const current = i === run.current_step && isRunning;
          const pending = !done && !current;
          return (
            <div
              key={step.id}
              className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                current ? "bg-blue-600/10 border-blue-600/40" :
                done ? "bg-green-900/10 border-green-900/30" :
                "bg-[#13161f] border-[#1e2433]"
              }`}
            >
              <div className="shrink-0 mt-0.5">
                {done ? <CheckCircle2 size={15} className="text-green-400" /> :
                 current ? <Clock size={15} className="text-blue-400 animate-pulse" /> :
                 <ChevronRight size={15} className="text-slate-600" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className={`text-sm font-medium ${current ? "text-blue-300" : done ? "text-green-300" : "text-slate-500"}`}>
                    {i + 1}. {step.name}
                  </p>
                  {step.human_gate && (
                    <span className="text-[10px] px-1 py-0.5 rounded bg-amber-900/30 text-amber-400 border border-amber-900/40">
                      human gate
                    </span>
                  )}
                </div>
                {step.description && (
                  <p className="text-xs text-slate-500 mt-0.5">{step.description}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {isRunning && currentStep && (
        <div className="bg-[#13161f] border border-blue-600/30 rounded-lg p-5">
          <p className="text-sm font-medium text-blue-300 mb-1">Current Step: {currentStep.name}</p>
          <p className="text-xs text-slate-400 mb-4">{currentStep.description}</p>
          <div className="space-y-3 mb-4">
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Outcome (optional)</label>
              <input
                value={outcome}
                onChange={(e) => setOutcome(e.target.value)}
                placeholder="e.g. approved, completed, skipped"
                className="w-full bg-[#0f1117] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600/50"
              />
            </div>
            <div>
              <label className="text-xs text-slate-500 mb-1 block">Notes (optional)</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full bg-[#0f1117] border border-[#1e2433] rounded px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600/50 resize-none"
              />
            </div>
          </div>
          <button
            onClick={handleAdvance}
            disabled={advancing}
            className="flex items-center gap-2 px-4 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-500 disabled:opacity-50 transition-colors"
          >
            {advancing ? <Loader2 size={14} className="animate-spin" /> : <ChevronRight size={14} />}
            {run.current_step === run.steps.length - 1 ? "Complete Workflow" : "Advance to Next Step"}
          </button>
        </div>
      )}

      <p className="text-xs text-slate-600 mt-5">Started {formatDate(run.created_at)} · Updated {formatDate(run.updated_at)}</p>
    </div>
  );
}
