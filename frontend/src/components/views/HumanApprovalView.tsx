import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  ShieldAlert, 
  Check, 
  X, 
  AlertTriangle, 
  Wrench, 
  FileText, 
  Send, 
  ArrowRight
} from 'lucide-react';
import type { ApprovalRequest } from '../../types';

export const HumanApprovalView: React.FC = () => {
  const { 
    tasks, 
    approveTaskAction, 
    rejectTaskAction, 
    activeApprovalModal, 
    setActiveTab,
    setSelectedTaskId
  } = useApp();

  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  const [selectedApprovalId, setSelectedApprovalId] = useState<string | null>(null);

  const pendingTasks = tasks.filter(t => t.status === 'WAITING_FOR_APPROVAL' && t.approvalRequest);

  const currentApproval = activeApprovalModal || 
    (selectedApprovalId ? pendingTasks.find(t => t.approvalRequest?.id === selectedApprovalId)?.approvalRequest : null) || 
    pendingTasks[0]?.approvalRequest;

  const approvalItem: ApprovalRequest | null = currentApproval || null;

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200 text-[11px] font-mono font-bold mb-2">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span>HUMAN-IN-THE-LOOP GUARDRAILS</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Pending Human Approvals</h2>
          <p className="text-xs text-slate-500 font-normal">
            Review high-risk actions before AgentX executes external communications or financial transactions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {pendingTasks.length > 1 && (
            <select
              value={approvalItem?.id || ''}
              onChange={(e) => setSelectedApprovalId(e.target.value)}
              className="bg-white text-slate-800 text-xs font-bold rounded-xl px-3 py-2 border border-slate-200 shadow-xs cursor-pointer"
            >
              {pendingTasks.map(t => (
                <option key={t.approvalRequest!.id} value={t.approvalRequest!.id}>
                  {t.approvalRequest!.id} - {t.title.slice(0, 25)}...
                </option>
              ))}
            </select>
          )}

          <div className="px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${pendingTasks.length > 0 ? 'bg-amber-500 animate-ping' : 'bg-emerald-500'}`}></span>
            <span>{pendingTasks.length} Pending Signoff</span>
          </div>
        </div>
      </div>

      {!approvalItem ? (
        <div className="glass-card rounded-2xl p-12 text-center border border-slate-200 bg-white/60 space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center mx-auto">
            <Check className="w-6 h-6 stroke-[3]" />
          </div>
          <h3 className="text-base font-bold text-slate-900">All Operations Clear</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            There are no pending actions requiring human approval at this moment. AI teammates are operating within their authorized guardrails.
          </p>
        </div>
      ) : (

      <div className="glass-card rounded-2xl p-6 md:p-8 border-2 border-amber-300 bg-amber-50/30 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold shadow-xs">
              <ShieldAlert className="w-7 h-7 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-extrabold text-slate-900">Approval Required</span>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-red-100 text-red-700 border border-red-200 uppercase">
                  Risk Level: {approvalItem.riskLevel}
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1 font-medium">
                Requested by <strong className="text-indigo-600 font-bold">{approvalItem.agentName}</strong> for Task <span className="font-mono text-indigo-700 font-bold">{approvalItem.taskId}</span>
              </p>
            </div>
          </div>

          <div className="text-right">
            <p className="text-[10px] uppercase font-mono text-slate-400 font-bold">Requested</p>
            <p className="text-xs text-slate-800 font-mono font-bold">{approvalItem.createdAt}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
              <p className="text-[11px] uppercase font-mono text-slate-400 font-bold flex items-center gap-1">
                <Wrench className="w-3.5 h-3.5 text-indigo-600" />
                Target Tool & Action
              </p>
              <p className="text-sm font-bold text-amber-800 font-mono">
                {approvalItem.toolName}
              </p>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
              <p className="text-[11px] uppercase font-mono text-slate-400 font-bold flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Why Approval is Required
              </p>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {approvalItem.whyRequired}
              </p>
            </div>

            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-2">
              <p className="text-[11px] uppercase font-mono text-slate-400 font-bold flex items-center gap-1">
                <Send className="w-3.5 h-3.5 text-emerald-600" />
                Proposed Action Outcome
              </p>
              <p className="text-xs text-slate-900 leading-relaxed font-bold">
                {approvalItem.proposedAction}
              </p>
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 flex flex-col justify-between">
            <div>
              <p className="text-[11px] uppercase font-mono text-slate-500 font-bold mb-2 flex items-center gap-1">
                <FileText className="w-3.5 h-3.5 text-indigo-600" />
                Payload Preview (JSON)
              </p>
              <pre className="text-[11px] font-mono text-indigo-900 bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto whitespace-pre-wrap leading-tight">
                {JSON.stringify(approvalItem.payloadPreview, null, 2)}
              </pre>
            </div>

            <div className="pt-3 border-t border-slate-200 text-[10px] text-slate-500 font-mono text-center font-bold">
              Agent Sandbox Lockdown: Active
            </div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
          <button
            onClick={() => {
              setSelectedTaskId(approvalItem.taskId);
              setActiveTab('task-execution');
            }}
            className="text-xs text-indigo-600 hover:underline font-bold flex items-center gap-1"
          >
            <span>View Task in Live Timeline</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <div className="flex items-center gap-3 w-full md:w-auto">
            {showRejectInput ? (
              <div className="flex items-center gap-2 flex-1">
                <input
                  type="text"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Reason for rejection..."
                  className="bg-white text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 text-slate-900 focus:outline-none focus:border-red-500 w-64 font-medium"
                />
                <button
                  onClick={() => rejectTaskAction(approvalItem.id, rejectionReason)}
                  className="px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-xs"
                >
                  Confirm Reject
                </button>
                <button
                  onClick={() => setShowRejectInput(false)}
                  className="px-3 py-2 text-xs text-slate-500 font-medium"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowRejectInput(true)}
                className="px-5 py-3 rounded-xl bg-white hover:bg-red-50 text-red-600 border border-red-200 text-xs font-bold transition-colors flex items-center gap-1.5 shadow-xs"
              >
                <X className="w-4 h-4" />
                <span>Reject</span>
              </button>
            )}

            <button
              onClick={() => approveTaskAction(approvalItem.id)}
              className="px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs shadow-md shadow-emerald-600/20 transition-all hover:scale-105 flex items-center gap-2"
            >
              <Check className="w-4 h-4 stroke-[3]" />
              <span>Approve & Continue Task</span>
            </button>
          </div>
        </div>
      </div>
      )}
    </div>
  );
};
