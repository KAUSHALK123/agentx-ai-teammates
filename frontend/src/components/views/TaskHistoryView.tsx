import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Search, 
  SlidersHorizontal, 
  Headphones, 
  BarChart3, 
  Workflow
} from 'lucide-react';
import type { AgentRole } from '../../types';

type HistoryFilterTab = 'ALL' | 'support' | 'sales' | 'operations' | 'WAITING' | 'FAILED';

export const TaskHistoryView: React.FC = () => {
  const { tasks, setSelectedTaskId, setActiveTab } = useApp();

  const [activeTabFilter, setActiveTabFilter] = useState<HistoryFilterTab>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Fallback demo tasks matching Reference Image 2 if tasks are still synchronizing
  const defaultHistoryRecords = [
    {
      id: 'TASK-C001',
      title: 'Investigate Customer C001 Order Issue',
      agentRole: 'support' as AgentRole,
      agentName: 'Support Lead',
      status: 'EXECUTING',
      dispatchDate: 'Oct 18, 2:45 PM',
      cycleTime: '2:45',
      result: 'IN PROGRESS',
      resultColor: 'text-slate-500'
    },
    {
      id: 'TASK-L409',
      title: 'Follow-up Lead L-409 Interaction',
      agentRole: 'sales' as AgentRole,
      agentName: 'Growth Engine',
      status: 'WAITING',
      dispatchDate: 'Oct 18, 1:20 PM',
      cycleTime: '-',
      result: 'NEEDS APPROVAL',
      resultColor: 'text-amber-600 font-bold'
    },
    {
      id: 'TASK-R701',
      title: 'Weekly Operational Report Gen',
      agentRole: 'operations' as AgentRole,
      agentName: 'Flow Architect',
      status: 'COMPLETED',
      dispatchDate: 'Oct 17, 11:30 AM',
      cycleTime: '0:32',
      result: 'SUCCESS',
      resultColor: 'text-emerald-600 font-bold'
    },
    {
      id: 'TASK-C902',
      title: 'Refund Process for #C-902',
      agentRole: 'support' as AgentRole,
      agentName: 'Support Lead',
      status: 'COMPLETED',
      dispatchDate: 'Oct 17, 9:15 AM',
      cycleTime: '4:12',
      result: 'SUCCESS',
      resultColor: 'text-emerald-600 font-bold'
    }
  ];

  // Map real tasks into table format with fallback
  const mappedRecords = (tasks && tasks.length > 0)
    ? tasks.map(t => {
        const isSupport = t.agentRole === 'support';
        const isSales = t.agentRole === 'sales';
        const agentName = isSupport ? 'Support Lead' : isSales ? 'Growth Engine' : 'Flow Architect';
        
        let result = 'SUCCESS';
        let resultColor = 'text-emerald-600 font-bold';
        if (t.status === 'WAITING_FOR_APPROVAL') {
          result = 'NEEDS APPROVAL';
          resultColor = 'text-amber-600 font-bold';
        } else if (t.status === 'EXECUTING' || t.status === 'PLANNING' || t.status === 'CREATED') {
          result = 'IN PROGRESS';
          resultColor = 'text-slate-500';
        } else if (t.status === 'FAILED' || t.status === 'ESCALATED') {
          result = 'FAILED';
          resultColor = 'text-red-500 font-bold';
        }

        const durationSec = Math.round((t.durationMs || 1200) / 1000);
        const mins = Math.floor(durationSec / 60);
        const secs = durationSec % 60;
        const cycleTime = t.status === 'WAITING_FOR_APPROVAL' ? '-' : `${mins}:${secs < 10 ? '0' : ''}${secs}`;

        return {
          id: t.id,
          title: t.title,
          agentRole: t.agentRole,
          agentName,
          status: t.status === 'WAITING_FOR_APPROVAL' ? 'WAITING' : t.status,
          dispatchDate: t.createdAt || 'Just now',
          cycleTime,
          result,
          resultColor
        };
      })
    : defaultHistoryRecords;

  // Filter tasks based on active tab and search
  const filteredRecords = mappedRecords.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          item.agentName.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (activeTabFilter === 'ALL') return true;
    if (activeTabFilter === 'support') return item.agentRole === 'support';
    if (activeTabFilter === 'sales') return item.agentRole === 'sales';
    if (activeTabFilter === 'operations') return item.agentRole === 'operations';
    if (activeTabFilter === 'WAITING') return item.status === 'WAITING' || item.result === 'NEEDS APPROVAL';
    if (activeTabFilter === 'FAILED') return item.status === 'FAILED' || item.result === 'FAILED';
    return true;
  });

  const getAgentIcon = (role: AgentRole) => {
    if (role === 'support') {
      return <Headphones className="w-4 h-4 text-blue-500" />;
    }
    if (role === 'sales') {
      return <BarChart3 className="w-4 h-4 text-emerald-500" />;
    }
    return <Workflow className="w-4 h-4 text-amber-500" />;
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase()) {
      case 'EXECUTING':
        return (
          <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-cyan-100/70 text-cyan-700 tracking-wider">
            EXECUTING
          </span>
        );
      case 'WAITING':
      case 'WAITING_FOR_APPROVAL':
        return (
          <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-amber-100/70 text-amber-800 tracking-wider">
            WAITING
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-emerald-100/70 text-emerald-700 tracking-wider">
            COMPLETED
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-red-100 text-red-700 tracking-wider">
            FAILED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-md text-[10px] font-mono font-bold bg-slate-100 text-slate-700 tracking-wider">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header matching Reference Image 2 */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="text-4xl font-display font-extrabold text-slate-900 tracking-tight">
          Task History
        </h1>

        {/* Right Filter & Search Bar */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter records..."
              className="bg-white/70 text-slate-800 text-xs pl-9 pr-4 py-2.5 rounded-full border border-slate-200/80 focus:outline-none focus:border-cyan-500 font-medium w-56 md:w-64 shadow-xs"
            />
          </div>

          <button
            onClick={() => {
              // Toggle filter modal or cycle filter
              setActiveTabFilter(prev => prev === 'ALL' ? 'WAITING' : 'ALL');
            }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-white/70 hover:bg-white text-slate-700 text-xs font-bold border border-slate-200/80 shadow-xs transition-all cursor-pointer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500" />
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs matching Image 2 */}
      <div className="flex items-center gap-8 border-b border-slate-200/60 text-xs font-semibold overflow-x-auto">
        <button
          onClick={() => setActiveTabFilter('ALL')}
          className={`pb-3 font-bold transition-all whitespace-nowrap cursor-pointer ${
            activeTabFilter === 'ALL' 
              ? 'text-cyan-600 border-b-2 border-cyan-500 font-extrabold' 
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          All Records
        </button>

        <button
          onClick={() => setActiveTabFilter('support')}
          className={`pb-3 font-bold transition-all whitespace-nowrap cursor-pointer ${
            activeTabFilter === 'support' 
              ? 'text-cyan-600 border-b-2 border-cyan-500 font-extrabold' 
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Support
        </button>

        <button
          onClick={() => setActiveTabFilter('sales')}
          className={`pb-3 font-bold transition-all whitespace-nowrap cursor-pointer ${
            activeTabFilter === 'sales' 
              ? 'text-cyan-600 border-b-2 border-cyan-500 font-extrabold' 
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Growth
        </button>

        <button
          onClick={() => setActiveTabFilter('operations')}
          className={`pb-3 font-bold transition-all whitespace-nowrap cursor-pointer ${
            activeTabFilter === 'operations' 
              ? 'text-cyan-600 border-b-2 border-cyan-500 font-extrabold' 
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Flow
        </button>

        <button
          onClick={() => setActiveTabFilter('WAITING')}
          className={`pb-3 font-bold transition-all whitespace-nowrap cursor-pointer ${
            activeTabFilter === 'WAITING' 
              ? 'text-cyan-600 border-b-2 border-cyan-500 font-extrabold' 
              : 'text-slate-500 hover:text-slate-900'
          }`}
        >
          Awaiting Approval
        </button>

        <button
          onClick={() => setActiveTabFilter('FAILED')}
          className={`pb-3 font-bold transition-all whitespace-nowrap cursor-pointer ${
            activeTabFilter === 'FAILED' 
              ? 'text-red-500 border-b-2 border-red-500 font-extrabold' 
              : 'text-red-400 hover:text-red-600'
          }`}
        >
          Failed
        </button>
      </div>

      {/* Large Table Container with rounded-[32px] matching Image 2 */}
      <div className="glass-card rounded-[32px] p-8 border border-white/70 shadow-xl bg-white/80 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-[10px] font-mono uppercase tracking-wider text-slate-400 border-b border-slate-100 pb-4">
                <th className="font-bold py-4 pr-6">TASK ENTITY</th>
                <th className="font-bold py-4 px-6">OWNER AGENT</th>
                <th className="font-bold py-4 px-6">STATUS</th>
                <th className="font-bold py-4 px-6">DISPATCH DATE</th>
                <th className="font-bold py-4 px-6">CYCLE TIME</th>
                <th className="font-bold py-4 pl-6">RESULT</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100/80 text-xs">
              {filteredRecords.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400 font-medium">
                    No records found matching the active filter.
                  </td>
                </tr>
              ) : (
                filteredRecords.map((record) => (
                  <tr
                    key={record.id}
                    onClick={() => {
                      setSelectedTaskId(record.id);
                      setActiveTab('task-execution');
                    }}
                    className="hover:bg-slate-50/70 transition-colors cursor-pointer group"
                  >
                    {/* Task Entity */}
                    <td className="py-5 pr-6 font-display font-bold text-slate-900 group-hover:text-cyan-600 transition-colors">
                      {record.title}
                    </td>

                    {/* Owner Agent */}
                    <td className="py-5 px-6">
                      <div className="flex items-center gap-2 font-medium text-slate-700">
                        {getAgentIcon(record.agentRole)}
                        <span>{record.agentName}</span>
                      </div>
                    </td>

                    {/* Status Pill */}
                    <td className="py-5 px-6">
                      {getStatusBadge(record.status)}
                    </td>

                    {/* Dispatch Date */}
                    <td className="py-5 px-6 text-slate-500 font-normal">
                      {record.dispatchDate}
                    </td>

                    {/* Cycle Time */}
                    <td className="py-5 px-6 font-mono text-slate-600">
                      {record.cycleTime}
                    </td>

                    {/* Result */}
                    <td className={`py-5 pl-6 font-mono text-[11px] tracking-wide ${record.resultColor}`}>
                      {record.result}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
export default TaskHistoryView;
