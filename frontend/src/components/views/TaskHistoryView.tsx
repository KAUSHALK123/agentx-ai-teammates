import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  History, 
  Search, 
  ArrowRight, 
  Bot, 
  PlayCircle,
  RotateCcw
} from 'lucide-react';
import type { AgentRole, TaskStatus } from '../../types';

export const TaskHistoryView: React.FC = () => {
  const { tasks, setSelectedTaskId, setActiveTab, refreshTasks } = useApp();

  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState<AgentRole | 'ALL'>('ALL');
  const [statusFilter, setStatusFilter] = useState<TaskStatus | 'ALL'>('ALL');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshTasks();
    } finally {
      setIsRefreshing(false);
    }
  };

  const filteredTasks = tasks.filter(t => {
    const matchesSearch = t.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          t.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          t.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'ALL' || t.agentRole === roleFilter;
    const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter;
    return matchesSearch && matchesRole && matchesStatus;
  });

  return (
    <div className="p-6 md:p-8 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <History className="w-3.5 h-3.5 text-indigo-600" />
            <span>AUDITABLE TASK HISTORY</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Workspace Task Log</h2>
          <p className="text-xs text-slate-500 font-medium">
            Complete record of autonomous tasks, tool calls, execution durations, and verifications.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            className={`p-2.5 rounded-xl bg-white border border-slate-200 text-slate-600 hover:text-indigo-600 hover:border-indigo-300 shadow-xs transition-colors ${
              isRefreshing ? 'animate-spin text-indigo-600' : ''
            }`}
            title="Refresh Tasks"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setActiveTab('create-task')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all"
          >
            <PlayCircle className="w-4 h-4" />
            <span>New Task</span>
          </button>
        </div>
      </div>

      <div className="glass-card p-4 rounded-2xl border border-slate-200 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ID, title, keywords..."
            className="w-full bg-slate-50 text-slate-900 text-xs pl-9 pr-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
          />
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value as any)}
            className="bg-slate-50 text-slate-800 text-xs font-semibold rounded-xl px-3 py-2.5 border border-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="ALL">All Agents</option>
            <option value="support">Support Teammate</option>
            <option value="sales">Sales Teammate</option>
            <option value="operations">Operations Teammate</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as any)}
            className="bg-slate-50 text-slate-800 text-xs font-semibold rounded-xl px-3 py-2.5 border border-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="WAITING_FOR_APPROVAL">Waiting for Approval</option>
            <option value="EXECUTING">Executing</option>
            <option value="ESCALATED">Escalated</option>
            <option value="FAILED">Failed</option>
          </select>
        </div>
      </div>

      <div className="glass-card rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
        <div className="p-4 border-b border-slate-200 bg-slate-50 text-[11px] font-mono uppercase text-slate-500 font-bold grid grid-cols-12 gap-4">
          <span className="col-span-2">Task ID & Agent</span>
          <span className="col-span-5">Title & Summary</span>
          <span className="col-span-2 text-center">Status</span>
          <span className="col-span-2 text-center">Duration</span>
          <span className="col-span-1 text-right">Action</span>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredTasks.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 font-medium">
              No tasks match the selected query and filters.
            </div>
          ) : (
            filteredTasks.map(t => (
              <div
                key={t.id}
                className="p-4 hover:bg-slate-50/80 transition-colors grid grid-cols-12 gap-4 items-center text-xs"
              >
                <div className="col-span-2 space-y-0.5">
                  <span className="font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">{t.id}</span>
                  <p className="text-[11px] text-slate-500 flex items-center gap-1 font-medium mt-1">
                    <Bot className="w-3 h-3 text-indigo-600" />
                    {t.agentName.split(' ')[0]}
                  </p>
                </div>

                <div className="col-span-5 space-y-0.5">
                  <p className="font-bold text-slate-900 truncate">{t.title}</p>
                  <p className="text-[11px] text-slate-500 truncate">{t.description}</p>
                </div>

                <div className="col-span-2 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono uppercase font-bold ${
                    t.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                    t.status === 'WAITING_FOR_APPROVAL' ? 'bg-amber-100 text-amber-800 border border-amber-300 animate-pulse' :
                    'bg-indigo-50 text-indigo-700 border border-indigo-200'
                  }`}>
                    {t.status === 'WAITING_FOR_APPROVAL' ? 'Approval' : t.status}
                  </span>
                </div>

                <div className="col-span-2 text-center font-mono text-slate-700 text-[11px] font-bold">
                  {(t.durationMs / 1000).toFixed(1)}s
                </div>

                <div className="col-span-1 text-right">
                  <button
                    onClick={() => {
                      setSelectedTaskId(t.id);
                      setActiveTab('task-execution');
                    }}
                    className="p-2 rounded-lg bg-slate-100 hover:bg-indigo-600 text-slate-600 hover:text-white transition-colors border border-slate-200"
                    title="Open Task Execution"
                  >
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
