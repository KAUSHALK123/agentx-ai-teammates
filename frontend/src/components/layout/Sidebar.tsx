import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Cpu, 
  ChevronsUpDown, 
  LayoutDashboard, 
  Users, 
  ClipboardList, 
  PlusCircle, 
  Layers, 
  BarChart3, 
  Settings, 
  LogOut,
  ShieldAlert
} from 'lucide-react';
import type { NavTab } from '../../types';

export const Sidebar: React.FC = () => {
  const { activeTab, setActiveTab, tasks } = useApp();

  const pendingApprovalsCount = tasks.filter(t => t.status === 'WAITING_FOR_APPROVAL').length;

  const mainNav: { id: NavTab; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
    { id: 'agents', label: 'AI Teammates', icon: <Users className="w-5 h-5" /> },
    { id: 'task-history', label: 'Task History', icon: <ClipboardList className="w-5 h-5" /> },
    { id: 'create-task', label: 'Create Task', icon: <PlusCircle className="w-5 h-5" /> },
    { id: 'approvals', label: 'Policy Approvals', icon: <ShieldAlert className="w-5 h-5" />, badge: pendingApprovalsCount },
  ];

  const ecosystemNav: { id: NavTab; label: string; icon: React.ReactNode }[] = [
    { id: 'integrations', label: 'Integrations', icon: <Layers className="w-5 h-5" /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="w-5 h-5" /> },
    { id: 'settings', label: 'Settings', icon: <Settings className="w-5 h-5" /> },
  ];

  return (
    <aside className="w-72 bg-white/40 backdrop-blur-xl border-r border-white/50 flex flex-col fixed inset-y-0 left-0 z-50 select-none">
      {/* Brand Header */}
      <div 
        className="p-8 flex items-center gap-3 cursor-pointer group"
        onClick={() => setActiveTab('welcome')}
      >
        <div className="w-10 h-10 bg-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
          <Cpu className="w-6 h-6 text-white" />
        </div>
        <span className="font-display font-bold text-2xl tracking-tight text-slate-800">AgentX</span>
      </div>

      {/* Workspace Selector */}
      <div className="px-6 py-2">
        <button 
          onClick={() => setActiveTab('settings')}
          className="w-full flex items-center gap-3 px-4 py-3 text-sm font-semibold text-slate-600 glass-card rounded-2xl hover:bg-white/60 transition-all"
        >
          <div className="w-6 h-6 bg-cyan-100 rounded-lg flex items-center justify-center">
            <span className="text-[10px] text-cyan-600 font-bold">AX</span>
          </div>
          <span className="truncate">Enterprise Ops</span>
          <ChevronsUpDown className="w-4 h-4 ml-auto text-slate-400 shrink-0" />
        </button>
      </div>

      {/* Navigation items */}
      <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto custom-scrollbar">
        {mainNav.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
                isActive
                  ? 'sidebar-active font-bold'
                  : 'text-slate-500 hover:bg-white/40 hover:text-slate-900'
              }`}
            >
              <div className="flex items-center gap-4">
                <span className={isActive ? 'text-cyan-500' : 'text-slate-400'}>{item.icon}</span>
                <span>{item.label}</span>
              </div>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500 text-white animate-pulse">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}

        <div className="pt-6 pb-2 px-6 text-[11px] font-bold text-slate-400 uppercase tracking-widest">
          Ecosystem
        </div>

        {ecosystemNav.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-4 px-4 py-3 text-sm font-semibold rounded-xl transition-all ${
                isActive
                  ? 'sidebar-active font-bold'
                  : 'text-slate-500 hover:bg-white/40 hover:text-slate-900'
              }`}
            >
              <span className={isActive ? 'text-cyan-500' : 'text-slate-400'}>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Profile Footer */}
      <div className="p-6 border-t border-white/50">
        <div className="flex items-center gap-3 p-2 rounded-2xl glass-card">
          <img 
            src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" 
            className="w-10 h-10 rounded-full border-2 border-white shadow-sm" 
            alt="Alex Rivera"
          />
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-bold truncate text-slate-800">Alex Rivera</p>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter truncate">Operations Director</p>
          </div>
          <button 
            onClick={() => setActiveTab('welcome')}
            className="text-slate-400 hover:text-cyan-500 transition-colors"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
