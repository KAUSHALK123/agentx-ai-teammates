import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { Search, X, Bot, PlayCircle, ShieldAlert, Workflow, ArrowRight } from 'lucide-react';
import type { NavTab } from '../../types';

export const SearchModal: React.FC = () => {
  const { isSearchOpen, setIsSearchOpen, setActiveTab, setSelectedTaskId, tasks } = useApp();
  const [query, setQuery] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(!isSearchOpen);
      }
      if (e.key === 'Escape' && isSearchOpen) {
        setIsSearchOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSearchOpen, setIsSearchOpen]);

  if (!isSearchOpen) return null;

  const filteredTasks = tasks.filter(t => 
    t.title.toLowerCase().includes(query.toLowerCase()) || 
    t.id.toLowerCase().includes(query.toLowerCase()) ||
    t.agentName.toLowerCase().includes(query.toLowerCase())
  );

  const quickNavs: { label: string; tab: NavTab; icon: React.ReactNode }[] = [
    { label: 'Create New Task', tab: 'create-task', icon: <PlayCircle className="w-4 h-4 text-indigo-600" /> },
    { label: 'View Pending Approvals', tab: 'approvals', icon: <ShieldAlert className="w-4 h-4 text-amber-600" /> },
    { label: 'AI Teammate Directory', tab: 'agents', icon: <Bot className="w-4 h-4 text-blue-600" /> },
    { label: 'Integrations & n8n Workflows', tab: 'integrations', icon: <Workflow className="w-4 h-4 text-purple-600" /> },
  ];

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-start justify-center pt-24 px-4 animate-in fade-in duration-200">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center gap-3">
          <Search className="w-5 h-5 text-indigo-600" />
          <input
            type="text"
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search tasks, agents, integrations..."
            className="w-full bg-transparent text-slate-800 placeholder-slate-400 text-sm font-medium focus:outline-none"
          />
          <button 
            onClick={() => setIsSearchOpen(false)}
            className="p-1 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-4 max-h-96 overflow-y-auto space-y-4">
          {!query && (
            <div>
              <p className="text-[10px] uppercase font-mono text-slate-400 font-bold mb-2">Quick Navigation</p>
              <div className="space-y-1">
                {quickNavs.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setActiveTab(item.tab);
                      setIsSearchOpen(false);
                    }}
                    className="w-full flex items-center justify-between p-2.5 rounded-xl bg-slate-50 hover:bg-indigo-50 text-slate-800 text-xs font-semibold transition-colors"
                  >
                    <div className="flex items-center gap-2.5">
                      {item.icon}
                      <span>{item.label}</span>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="text-[10px] uppercase font-mono text-slate-400 font-bold mb-2">
              Tasks ({filteredTasks.length})
            </p>
            <div className="space-y-1.5">
              {filteredTasks.map(t => (
                <button
                  key={t.id}
                  onClick={() => {
                    setSelectedTaskId(t.id);
                    setActiveTab('task-execution');
                    setIsSearchOpen(false);
                  }}
                  className="w-full text-left p-3 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors flex items-center justify-between"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-100">{t.id}</span>
                      <span className="text-xs font-semibold text-slate-800 truncate max-w-sm">{t.title}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5">{t.agentName} • {t.status}</p>
                  </div>
                  <span className="text-xs text-indigo-600 font-bold hover:underline flex items-center gap-1">
                    Open Task <ArrowRight className="w-3 h-3" />
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="p-2.5 bg-slate-50 border-t border-slate-200 text-center text-[11px] text-slate-500 flex items-center justify-between px-4">
          <span>Press <kbd className="px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-700 font-mono font-bold">ESC</kbd> to close</span>
          <span>AgentX Search Engine</span>
        </div>
      </div>
    </div>
  );
};
