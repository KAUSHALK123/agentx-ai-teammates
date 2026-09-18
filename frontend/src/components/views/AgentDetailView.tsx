import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { agentsApi } from '../../api';
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
  Activity,
  Loader2,
  AlertTriangle,
  Inbox
} from 'lucide-react';
import type { AgentInfo } from '../../types';

export const AgentDetailView: React.FC = () => {
  const { selectedAgentRole, setSelectedAgentRole, agents, tasks, setActiveTab, setSelectedTaskId, isBackendConnected } = useApp();

  const [backendAgent, setBackendAgent] = useState<AgentInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch agent details from backend API when connected
  useEffect(() => {
    let isMounted = true;

    async function fetchAgentDetails() {
      setIsLoading(true);
      setError(null);
      try {
        const res = await agentsApi.getAgent(selectedAgentRole);
        if (isMounted && res) {
          // Map backend response schema into AgentInfo format
          const mappedAgent: AgentInfo = {
            name: res.name || (selectedAgentRole === 'support' ? 'Support Teammate' : selectedAgentRole === 'sales' ? 'Sales Teammate' : 'Operations Teammate'),
            role: selectedAgentRole,
            title: res.role || (selectedAgentRole === 'support' ? 'Customer Resolution Specialist' : selectedAgentRole === 'sales' ? 'Growth & Lead Specialist' : 'Operations & Logistics Manager'),
            description: res.description || 'Specialized AI teammate built for autonomous enterprise execution.',
            status: 'Online',
            avatar: selectedAgentRole,
            capabilities: res.capabilities || res.responsibilities || [
              'Extract customer entities & intent',
              'Investigate order fulfillment & carrier tracking',
              'Inspect transaction settlement',
              'Formulate verified response recommendations'
            ],
            tools: (res.available_tools || []).map((tName: string) => ({
              id: tName,
              name: tName,
              category: 'API Integration',
              status: 'Active',
              icon: tName.includes('Shopify') || tName.includes('Order') ? 'ShoppingBag' :
                    tName.includes('Stripe') || tName.includes('Refund') ? 'CreditCard' :
                    tName.includes('Email') || tName.includes('Gmail') ? 'Mail' : 'Wrench'
            })),
            tasksCompleted: 1420,
            successRate: 98.4,
            avgResponseTime: '1.4s',
            uptime: '99.9%',
            handledTaskTypes: selectedAgentRole === 'support'
              ? ['Customer Complaints', 'Delayed Order Investigations', 'Refund Authorizations', 'Review Analyses']
              : selectedAgentRole === 'sales'
              ? ['Lead Enrichment', 'HubSpot Contact Sync', 'Salesforce Proposals']
              : ['Inventory Purchase Orders', 'n8n Workflow Execution', 'Logistics Audits']
          };
          setBackendAgent(mappedAgent);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load agent details from backend.');
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    if (isBackendConnected) {
      fetchAgentDetails();
    } else {
      setBackendAgent(null);
      setIsLoading(false);
    }

    return () => { isMounted = false; };
  }, [selectedAgentRole, isBackendConnected]);

  const agent = backendAgent || agents[selectedAgentRole] || agents.support;

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
      {/* Navigation & Teammate Selector Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
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

      {/* Loading State Skeleton */}
      {isLoading && (
        <div className="glass-card rounded-2xl p-12 text-center space-y-4">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin mx-auto" />
          <p className="text-xs text-slate-500 font-medium">Fetching real-time agent profile from backend...</p>
        </div>
      )}

      {/* Error State Banner */}
      {error && !isLoading && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>{error} Showing cached agent profile.</span>
          </div>
          <button
            onClick={() => setSelectedAgentRole(selectedAgentRole)}
            className="px-3 py-1 bg-white border border-amber-300 rounded-lg font-bold text-amber-900 text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Agent Identity Card */}
      {!isLoading && (
        <div className="glass-card rounded-2xl p-6 md:p-8 border border-slate-200 relative overflow-hidden">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20 shrink-0">
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
      )}

      {/* Capabilities & Tools Split */}
      {!isLoading && (
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
      )}

      {/* Recent Tasks Handled */}
      {!isLoading && (
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-600" />
            <span>Recent Tasks Handled by {agent.name}</span>
          </h3>

          {agentTasks.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 font-medium space-y-2">
              <Inbox className="w-8 h-8 text-slate-400 mx-auto" />
              <p>No recent tasks logged for {agent.name}.</p>
              <button
                onClick={() => setActiveTab('create-task')}
                className="text-indigo-600 hover:underline font-bold"
              >
                Start a new support task →
              </button>
            </div>
          ) : (
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
                  <div className="space-y-1 max-w-md">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">
                        {t.id}
                      </span>
                      <span className="text-xs font-bold text-slate-900 truncate">{t.title}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate">{t.description}</p>
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
          )}
        </div>
      )}
    </div>
  );
};
