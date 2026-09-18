import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Bot, 
  PlayCircle, 
  ArrowRight, 
  LifeBuoy, 
  Briefcase, 
  Layers, 
  Zap, 
  Wrench,
  ShieldCheck
} from 'lucide-react';
import type { AgentRole } from '../../types';

export const AgentsView: React.FC = () => {
  const { agents, setSelectedAgentRole, setActiveTab } = useApp();

  const handleOpenAgent = (role: AgentRole) => {
    setSelectedAgentRole(role);
    setActiveTab('agent-detail');
  };

  const handleStartTask = (role: AgentRole) => {
    setSelectedAgentRole(role);
    setActiveTab('create-task');
  };

  return (
    <div className="p-6 md:p-8 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <Bot className="w-3.5 h-3.5 text-indigo-600" />
            <span>AUTONOMOUS WORKFORCE TEAMS</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">AI Teammate Directory</h2>
          <p className="text-xs text-slate-500">
            Inspect your specialized AI agents, active capabilities, performance history, and tool permissions.
          </p>
        </div>

        <button
          onClick={() => setActiveTab('create-task')}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold shadow-sm transition-all"
        >
          <PlayCircle className="w-4 h-4" />
          <span>Dispatch Task to Agent</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Object.values(agents).map((agent) => {
          const isSupport = agent.role === 'support';
          const isSales = agent.role === 'sales';

          const accentBg = isSupport ? 'bg-indigo-50 border-indigo-100 text-indigo-600' :
                           isSales ? 'bg-blue-50 border-blue-100 text-blue-600' :
                           'bg-purple-50 border-purple-100 text-purple-600';

          const AgentIcon = isSupport ? LifeBuoy : isSales ? Briefcase : Layers;

          return (
            <div
              key={agent.role}
              className="glass-card rounded-2xl p-6 border border-slate-200 hover:border-slate-300 transition-all flex flex-col justify-between space-y-6"
            >
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${accentBg} border shadow-xs`}>
                      <AgentIcon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-slate-900">{agent.name}</h3>
                      <p className="text-xs text-slate-500">{agent.title}</p>
                    </div>
                  </div>

                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                    {agent.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed font-normal">
                  {agent.description}
                </p>

                <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase font-mono font-bold">Completed</p>
                    <p className="text-sm font-extrabold text-slate-900">{agent.tasksCompleted.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase font-mono font-bold">Success Rate</p>
                    <p className="text-sm font-extrabold text-emerald-600">{agent.successRate}%</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <p className="text-[10px] uppercase font-mono text-slate-500 font-bold flex items-center gap-1">
                    <Zap className="w-3 h-3 text-indigo-600" />
                    Capabilities ({agent.capabilities.length})
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {agent.capabilities.slice(0, 4).map((cap, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 rounded bg-slate-100 border border-slate-200 text-slate-700 text-[11px] font-medium"
                      >
                        {cap}
                      </span>
                    ))}
                    {agent.capabilities.length > 4 && (
                      <span className="px-2 py-1 rounded bg-slate-100 text-slate-500 text-[11px] font-medium">
                        +{agent.capabilities.length - 4} more
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                  <span className="flex items-center gap-1">
                    <Wrench className="w-3.5 h-3.5 text-slate-400" />
                    {agent.tools.length} Tools Connected
                  </span>
                  <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Guardrails Active
                  </span>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleOpenAgent(agent.role)}
                  className="w-full py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold border border-slate-200 transition-colors"
                >
                  Open Agent
                </button>
                <button
                  onClick={() => handleStartTask(agent.role)}
                  className="w-full py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-xs transition-all flex items-center justify-center gap-1"
                >
                  <span>Start Task</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
