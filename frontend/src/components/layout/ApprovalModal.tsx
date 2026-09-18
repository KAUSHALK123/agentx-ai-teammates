import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ShieldAlert, X } from 'lucide-react';

export const ApprovalModal: React.FC = () => {
  const { activeApprovalModal, setActiveApprovalModal, approveTaskAction, rejectTaskAction } = useApp();
  const [rejectionReason, setRejectionReason] = useState('');
  const [showRejectInput, setShowRejectInput] = useState(false);

  if (!activeApprovalModal) return null;

  return (
    <div className="fixed inset-0 z-[100] bg-slate-900/30 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="glass-card rounded-[48px] w-full max-w-2xl shadow-2xl border-white/60 overflow-hidden">
        {/* Modal Header */}
        <div className="p-8 md:p-10 border-b border-white/50 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-orange-100 rounded-2xl flex items-center justify-center shadow-xs">
              <ShieldAlert className="w-7 h-7 text-orange-500 animate-pulse" />
            </div>
            <div>
              <h3 className="text-2xl font-display font-bold text-slate-900">Policy Intercept</h3>
              <p className="text-slate-500 text-sm font-medium">
                High Risk: <span className="font-bold text-amber-700">{activeApprovalModal.riskLevel}</span>
              </p>
            </div>
          </div>
          <button 
            onClick={() => setActiveApprovalModal(null)}
            className="w-10 h-10 rounded-full bg-white/50 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-all shadow-xs"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-8 md:p-10 space-y-8">
          {/* Reason Callout */}
          <div className="p-6 bg-orange-50/70 border border-orange-200/70 rounded-3xl">
            <p className="text-slate-700 leading-relaxed text-sm font-medium">
              <span className="font-bold text-orange-600">Reason:</span> {activeApprovalModal.whyRequired}
            </p>
          </div>

          {/* Draft Payload Preview */}
          <div className="bg-white/60 border border-white/80 rounded-[32px] p-6 md:p-8">
            <div className="flex justify-between items-center mb-4">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                Target Tool & Action: <code className="text-cyan-700 font-mono font-bold">{activeApprovalModal.toolName}</code>
              </span>
              <span className="text-xs font-bold text-slate-700">Payload Preview</span>
            </div>
            
            <div className="bg-slate-900 p-4 rounded-2xl border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto max-h-40 leading-relaxed">
              {JSON.stringify(activeApprovalModal.payloadPreview, null, 2)}
            </div>
          </div>

          {/* Actions Footer */}
          <div className="flex flex-col sm:flex-row gap-4">
            {showRejectInput ? (
              <div className="flex items-center gap-2 flex-1">
                <input
                  type="text"
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Reason for requesting edit..."
                  className="flex-1 bg-white text-xs px-4 py-3 rounded-2xl border border-slate-200 text-slate-800 focus:outline-none focus:border-red-500 font-medium"
                />
                <button
                  onClick={() => rejectTaskAction(activeApprovalModal.id, rejectionReason)}
                  className="px-5 py-3 rounded-2xl bg-red-600 hover:bg-red-700 text-white text-xs font-bold shadow-md"
                >
                  Confirm Reject
                </button>
                <button
                  onClick={() => setShowRejectInput(false)}
                  className="px-3 py-3 text-xs text-slate-500 font-medium"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowRejectInput(true)}
                className="flex-1 py-4 glass-card border-slate-200 text-slate-600 font-bold rounded-2xl hover:bg-white/80 transition-all text-sm"
              >
                Request Edit
              </button>
            )}

            <button
              onClick={() => approveTaskAction(activeApprovalModal.id)}
              className="flex-2 bg-cyan-500 hover:bg-cyan-600 text-white font-bold py-4 px-10 rounded-2xl shadow-lg shadow-cyan-500/20 transition-all hover:scale-105 text-sm"
            >
              Authorize Dispatch
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
