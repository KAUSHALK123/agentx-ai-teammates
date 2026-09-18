import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  CheckCircle2, 
  ShieldCheck, 
  Wrench, 
  PlayCircle, 
  ArrowLeft, 
  Zap, 
  LifeBuoy, 
  Briefcase, 
  Layers, 
  Database, 
  CreditCard, 
  Mail, 
  ShoppingBag, 
  Search, 
  Send, 
  Calendar, 
  FileSpreadsheet, 
  Workflow, 
  Server, 
  Truck, 
  MessageSquare,
  Activity
} from 'lucide-react';

export const AgentDetailView: React.FC = () => {
  const { selectedAgentRole, setSelectedAgentRole, agents, tasks, setActiveTab, setSelectedTaskId } = useApp();

  const agent = agents[selectedAgentRole] || agents.support;

  const isSupport = agent.role === 'support';
  const isSales = agent.role === 'sales';

  const AgentIcon = isSupport ? LifeBuoy : isSales ? Briefcase : Layers;

  const agentTasks = tasks.filter(t => t.agentRole === agent.role);

  const renderToolIcon = (iconName: string) => {
    switch (iconName) {
      case 'Database': return <Database className="w-4 h-4 text-indigo-600" />;
      case 'ShoppingBag': return <ShoppingBag className="w-4 h-4 text-emerald-600" />;
      case 'CreditCard': return <CreditCard className="w-4 h-4 text-amber-600" />;
      case 'LifeBuoy': return <LifeBuoy className="w-4 h-4 text-blue-600" />;
      case 'Mail': return <Mail className="w-4 h-4 text-pink-600" />;
      case 'Briefcase': return <Briefcase className="w-4 h-4 text-indigo-600" />;
      case 'Search': return <Search className="w-4 h-4 text-cyan-600" />;
      case 'Send': return <Send className="w-4 h-4 text-emerald-600" />;
      case 'Calendar': return <Calendar className="w-4 h-4 text-purple-600" />;
      case 'FileSpreadsheet': return <FileSpreadsheet className="w-4 h-4 text-green-600" />;
      case 'Workflow': return <Workflow className="w-4 h-4 text-orange-600" />;
      case 'Layers': return <Layers className="w-4 h-4 text-indigo-600" />;
      case 'Truck': return <Truck className="w-4 h-4 text-yellow-600" />;
      case 'Server': return <Server className="w-4 h-4 text-blue-600" />;
      case 'MessageSquare': return <MessageSquare className="w-4 h-4 text-pink-600" />;
      default: return <Wrench className="w-4 h-4 text-slate-500" />;
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8">
      <div className="flex items-center justify-between">
        <button
          onClick={() => setActiveTab('agents')}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 font-semibold transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Agents</span>
        </button>

        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setSelectedAgentRole('support')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              selectedAgentRole === 'support' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Support Teammate
          </button>
          <button
            onClick={() => setSelectedAgentRole('sales')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              selectedAgentRole === 'sales' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Sales Teammate
          </button>
          <button
            onClick={() => setSelectedAgentRole('operations')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              selectedAgentRole === 'operations' ? 'bg-purple-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Operations Teammate
          </button>
        </div>
      </div>

      <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-200 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20">
              <AgentIcon className="w-8 h-8" />
            </div>

            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-extrabold text-slate-900">{agent.name}</h2>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                  {agent.status} • {agent.uptime} Uptime
                </span>
              </div>
              <p className="text-sm font-bold text-indigo-600 mt-0.5">{agent.title}</p>
              <p className="text-xs text-slate-600 max-w-2xl mt-2 leading-relaxed font-normal">{agent.description}</p>
            </div>
          </div>

          <button
            onClick={() => setActiveTab('create-task')}
            className="flex items-center gap-2 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold shadow-md shadow-indigo-600/20 transition-all hover:scale-105 shrink-0"
          >
            <PlayCircle className="w-4 h-4" />
            <span>Start Task with {agent.name.split(' ')[0]}</span>
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slate-100">
          <div>
            <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Total Tasks Handled</p>
            <p className="text-xl font-extrabold text-slate-900 mt-1">{agent.tasksCompleted.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Success Rate</p>
            <p className="text-xl font-extrabold text-emerald-600 mt-1">{agent.successRate}%</p>
          </div>
          <div>
            <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Avg Execution Speed</p>
            <p className="text-xl font-extrabold text-indigo-600 mt-1">{agent.avgResponseTime}</p>
          </div>
          <div>
            <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Security Guardrails</p>
            <p className="text-xl font-extrabold text-purple-600 mt-1 flex items-center gap-1">
              <ShieldCheck className="w-5 h-5 text-purple-600" />
              Strict Sandbox
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Zap className="w-4 h-4 text-indigo-600" />
            <span>Role Capabilities ({agent.capabilities.length})</span>
          </h3>

          <div className="space-y-2.5">
            {agent.capabilities.map((cap, idx) => (
              <div
                key={idx}
                className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 font-medium"
              >
                <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
                <span>{cap}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Wrench className="w-4 h-4 text-purple-600" />
            <span>Available Sandboxed Tools ({agent.tools.length})</span>
          </h3>

          <div className="space-y-2.5">
            {agent.tools.map((tool, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                    {renderToolIcon(tool.icon)}
                  </div>
                  <div>
                    <p className="font-bold text-slate-900">{tool.name}</p>
                    <p className="text-[10px] text-slate-500 font-semibold">{tool.category}</p>
                  </div>
                </div>

                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                  tool.status === 'Active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                  'bg-amber-50 text-amber-700 border border-amber-200'
                }`}>
                  {tool.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-600" />
          <span>Recent Tasks Handled by {agent.name}</span>
        </h3>

        <div className="space-y-3">
          {agentTasks.map(t => (
            <div
              key={t.id}
              onClick={() => {
                setSelectedTaskId(t.id);
                setActiveTab('task-execution');
              }}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-indigo-300 hover:bg-slate-100/80 cursor-pointer transition-all flex items-center justify-between"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                    {t.id}
                  </span>
                  <span className="text-xs font-bold text-slate-900">{t.title}</span>
                </div>
                <p className="text-[11px] text-slate-500">{t.description}</p>
              </div>

              <div className="text-right space-y-1">
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase font-bold">
                  {t.status}
                </span>
                <p className="text-[10px] text-slate-400 font-mono">{t.createdAt}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
