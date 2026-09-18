import React from 'react';
import { useApp } from '../../context/AppContext';
import { Search, Bell, Plus, ShieldAlert } from 'lucide-react';

export const Header: React.FC = () => {
  const { setActiveTab, setIsSearchOpen, tasks, setActiveApprovalModal } = useApp();

  const pendingApprovals = tasks.filter(t => t.status === 'WAITING_FOR_APPROVAL');

  return (
    <header className="h-20 bg-white/30 backdrop-blur-xl border-b border-white/50 px-10 flex items-center justify-between sticky top-0 z-40">
      {/* Search Input */}
      <div className="flex items-center gap-6 flex-1 max-w-2xl">
        <div className="relative w-full group cursor-pointer" onClick={() => setIsSearchOpen(true)}>
          <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-cyan-500 transition-colors" />
          <input
            type="text"
            readOnly
            placeholder="Search agents, tools, or global tasks..."
            className="w-full pl-12 pr-6 py-3 bg-white/50 border border-white/80 rounded-2xl text-sm focus:outline-none focus:ring-4 focus:ring-cyan-500/10 focus:bg-white/80 transition-all cursor-pointer text-slate-700 font-medium"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        {/* System Status Pill */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 glass-card rounded-full shadow-xs">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">System Online</span>
        </div>

        {/* Pending Approvals Pill */}
        {pendingApprovals.length > 0 && (
          <button
            onClick={() => {
              const pendingTask = pendingApprovals[0];
              if (pendingTask.approvalRequest) {
                setActiveApprovalModal(pendingTask.approvalRequest);
              } else {
                setActiveTab('approvals');
              }
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-700 text-xs font-bold hover:bg-amber-500/20 transition-all animate-pulse"
          >
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>{pendingApprovals.length} Approval Required</span>
          </button>
        )}

        {/* Notifications Bell */}
        <button 
          onClick={() => setIsSearchOpen(true)}
          className="w-10 h-10 rounded-full glass-card flex items-center justify-center text-slate-500 hover:text-cyan-500 transition-all relative shadow-xs"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-2 right-2 w-2.5 h-2.5 bg-cyan-500 rounded-full border-2 border-white"></span>
        </button>

        {/* New Task CTA Button */}
        <button
          onClick={() => setActiveTab('create-task')}
          className="flex items-center gap-2 bg-cyan-500 hover:bg-cyan-600 text-white px-6 py-3 rounded-2xl text-sm font-bold transition-all shadow-lg shadow-cyan-500/25 hover:scale-105"
        >
          <Plus className="w-4 h-4" />
          <span>New Task</span>
        </button>
      </div>
    </header>
  );
};
