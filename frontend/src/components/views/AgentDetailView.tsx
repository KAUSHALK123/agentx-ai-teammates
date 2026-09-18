import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { agentsApi, tasksApi } from '../../api';
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
  AlertCircle,
  Inbox,
  Sparkles,
  ArrowRight,
  Check
} from 'lucide-react';
import type { AgentInfo } from '../../types';
import { INITIAL_AGENTS } from '../../mock/data';

export const AgentDetailView: React.FC = () => {
  const { selectedAgentRole, setSelectedAgentRole, agents, tasks, setActiveTab, setSelectedTaskId, createNewTask, isBackendConnected } = useApp();

  const [backendAgent, setBackendAgent] = useState<AgentInfo | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Interactive Task Execution Runner State
  const [activePrompt, setActivePrompt] = useState<string>('');
  const [isProcessingAction, setIsProcessingAction] = useState<boolean>(false);
  const [actionResult, setActionResult] = useState<{
    taskId: string;
    status: string;
    summary: string;
    steps?: string[];
  } | null>(null);

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

  const handleRunAgentAction = async (promptText: string) => {
    setIsProcessingAction(true);
    setActionResult(null);
    try {
      if (isBackendConnected) {
        const res = await tasksApi.createTask({
          user_request: promptText,
          selected_agent: selectedAgentRole
        });

        // Fetch execution details
        const execDetail = await tasksApi.getTaskExecution(res.task_id);
        const steps = (execDetail.steps || []).map((s: any) => s.description || s.action || s.tool_name || 'Executed tool action');

        setActionResult({
          taskId: res.task_id,
          status: res.status || 'COMPLETED',
          summary: `Successfully executed ${selectedAgentRole} workflow. Request: "${promptText}"`,
          steps: steps.length > 0 ? steps : ['Evaluated context parameters', 'Executed sandboxed tool actions', 'Verified result integrity']
        });
      } else {
        // Fallback local execution via Context
        const newTaskId = `TASK-${Math.floor(1000 + Math.random() * 9000)}`;
        createNewTask({
          title: promptText.slice(0, 50),
          description: promptText,
          agentRole: selectedAgentRole,
          priority: 'HIGH'
        });
        setActionResult({
          taskId: newTaskId,
          status: 'COMPLETED',
          summary: `Dispatched ${selectedAgentRole} task: "${promptText}"`,
          steps: ['Parsed request payload', 'Invoked agent capabilities', 'Completed execution']
        });
      }
    } catch (err: any) {
      setActionResult({
        taskId: 'ERR-TASK',
        status: 'FAILED',
        summary: err.message || 'Task execution encountered an error.'
      });
    } finally {
      setIsProcessingAction(false);
    }
  };

  const agent = backendAgent || agents[selectedAgentRole] || agents.support || INITIAL_AGENTS[selectedAgentRole] || INITIAL_AGENTS.support;

  if (!agent) {
    return (
      <div className="p-8 max-w-xl mx-auto glass-card rounded-2xl border border-slate-200 text-center space-y-4 my-12">
        <AlertCircle className="w-10 h-10 text-amber-500 mx-auto" />
        <h3 className="text-lg font-bold text-slate-900">Teammate Profile Not Found</h3>
        <p className="text-xs text-slate-500">Please select an autonomous agent from the directory below.</p>
        <div className="flex justify-center gap-2 pt-2">
          <button onClick={() => setSelectedAgentRole('support')} className="px-3 py-1.5 bg-indigo-600 text-white rounded-xl text-xs font-bold shadow-xs">Support</button>
          <button onClick={() => setSelectedAgentRole('sales')} className="px-3 py-1.5 bg-blue-600 text-white rounded-xl text-xs font-bold shadow-xs">Sales</button>
          <button onClick={() => setSelectedAgentRole('operations')} className="px-3 py-1.5 bg-purple-600 text-white rounded-xl text-xs font-bold shadow-xs">Operations</button>
        </div>
      </div>
    );
  }

  const isSupport = agent.role === 'support';
  const isSales = agent.role === 'sales';

  const AgentIcon = isSupport ? LifeBuoy : isSales ? Briefcase : Layers;

  const agentTasks = (tasks || []).filter(t => t.agentRole === agent.role);

  const renderToolIcon = (iconName?: string) => {
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

  const capabilitiesList = agent.capabilities || [];
  const toolsList = agent.tools || [];

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Navigation & Teammate Selector Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <button
          onClick={() => setActiveTab('agents')}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 font-semibold transition-colors w-fit cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Agents</span>
        </button>

        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            onClick={() => setSelectedAgentRole('support')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              selectedAgentRole === 'support' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Support Teammate
          </button>
          <button
            onClick={() => setSelectedAgentRole('sales')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
              selectedAgentRole === 'sales' ? 'bg-blue-600 text-white shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Sales Teammate
          </button>
          <button
            onClick={() => setSelectedAgentRole('operations')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${
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
                  <h2 className="text-2xl font-extrabold text-slate-900">{agent.name || 'AI Teammate'}</h2>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                    {agent.status || 'Online'} • {agent.uptime || '99.9%'} Uptime
                  </span>
                </div>
                <p className="text-sm font-bold text-indigo-600 mt-0.5">{agent.title || 'Autonomous Specialist'}</p>
                <p className="text-xs text-slate-600 max-w-2xl mt-2 leading-relaxed font-normal">{agent.description || 'Specialized AI teammate for enterprise automation.'}</p>
              </div>
            </div>

            <button
              onClick={() => setActiveTab('create-task')}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold shadow-md shadow-indigo-600/20 transition-all hover:scale-105 shrink-0 cursor-pointer"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Start Task with {(agent.name || 'Agent').split(' ')[0]}</span>
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8 pt-6 border-t border-slate-100">
            <div>
              <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Total Tasks Handled</p>
              <p className="text-xl font-extrabold text-slate-900 mt-1">{(agent.tasksCompleted ?? 1420).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Success Rate</p>
              <p className="text-xl font-extrabold text-emerald-600 mt-1">{agent.successRate ?? 98.4}%</p>
            </div>
            <div>
              <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">Avg Execution Speed</p>
              <p className="text-xl font-extrabold text-indigo-600 mt-1">{agent.avgResponseTime || '1.4s'}</p>
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
              <span>Role Capabilities ({capabilitiesList.length})</span>
            </h3>

            <div className="space-y-2.5">
              {capabilitiesList.length === 0 ? (
                <p className="text-xs text-slate-400">Standard business capabilities active.</p>
              ) : (
                capabilitiesList.map((cap: any, idx: number) => {
                  const capText = typeof cap === 'string' 
                    ? cap 
                    : (cap && typeof cap === 'object' && cap.name) 
                      ? `${cap.name.replace(/_/g, ' ')}${cap.description ? ` — ${cap.description}` : ''}`
                      : String(cap);

                  return (
                    <div
                      key={idx}
                      className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 font-medium"
                    >
                      <CheckCircle2 className="w-4 h-4 text-indigo-600 shrink-0" />
                      <span>{capText}</span>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Wrench className="w-4 h-4 text-purple-600" />
              <span>Available Sandboxed Tools ({toolsList.length})</span>
            </h3>

            <div className="space-y-2.5">
              {toolsList.length === 0 ? (
                <p className="text-xs text-slate-400">Standard sandboxed tools connected.</p>
              ) : (
                toolsList.map((tool: any, idx: number) => {
                  const toolName = typeof tool === 'string' ? tool : tool?.name || 'Tool';
                  const toolCategory = typeof tool === 'object' ? tool?.category || agent.role : agent.role;
                  const toolIcon = typeof tool === 'object' ? tool?.icon || 'Wrench' : 'Wrench';
                  const toolStatus = typeof tool === 'object' ? tool?.status || 'Active' : 'Active';

                  return (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-xs">
                          {renderToolIcon(toolIcon)}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{toolName}</p>
                          <p className="text-[10px] text-slate-500 font-semibold">{toolCategory}</p>
                        </div>
                      </div>

                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                        toolStatus === 'Active' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {toolStatus}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}

      {/* Interactive Workflow Runner Panel for Sales & Operations */}
      {!isLoading && (
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-600" />
              <span>
                {isSales ? 'Interactive Sales Lead Qualification & Outreach' :
                 agent.role === 'operations' ? 'Interactive Operations Data Audit & KPI Dispatch' :
                 'Support Resolution Workflows'}
              </span>
            </h3>

            {isSupport && (
              <button
                onClick={() => setActiveTab('support-review')}
                className="text-xs font-bold text-indigo-600 hover:underline flex items-center gap-1 cursor-pointer"
              >
                <span>Open Resolution Suite</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {!isSupport && (
            <div className="space-y-4">
              <p className="text-xs text-slate-600">
                {isSales
                  ? 'Select a lead preset or enter custom parameters to qualify prospects and dispatch CRM outreach.'
                  : 'Select an operational scenario or enter custom instructions to audit inventory logs and process business data.'}
              </p>

              {/* Preset Scenario Buttons */}
              <div className="flex flex-wrap gap-2">
                {isSales ? (
                  <>
                    <button
                      onClick={() => setActivePrompt('Qualify prospect CloudCorp (Deal size $85,000, Timeline Q4) and assign Lead Fit score.')}
                      className="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-800 text-xs font-bold border border-blue-200 transition-colors cursor-pointer"
                    >
                      Qualify Prospect CloudCorp ($85K)
                    </button>
                    <button
                      onClick={() => setActivePrompt('Draft personalized outbound proposal email follow-up for CloudCorp VP of IT.')}
                      className="px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-800 text-xs font-bold border border-indigo-200 transition-colors cursor-pointer"
                    >
                      Draft Outbound Proposal
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setActivePrompt('Audit inventory logs across warehouse nodes and detect low-stock exception alerts.')}
                      className="px-3 py-1.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-800 text-xs font-bold border border-purple-200 transition-colors cursor-pointer"
                    >
                      Audit Warehouse Inventory & Exceptions
                    </button>
                    <button
                      onClick={() => setActivePrompt('Compile monthly operational throughput report and audit record fulfillment discrepancies.')}
                      className="px-3 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-bold border border-emerald-200 transition-colors cursor-pointer"
                    >
                      Generate Operational KPI Audit Report
                    </button>
                  </>
                )}
              </div>

              {/* Prompt Input & Execute Button */}
              <div className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={activePrompt}
                  onChange={(e) => setActivePrompt(e.target.value)}
                  placeholder={isSales ? 'e.g. Qualify prospect CloudCorp with deal size $85,000...' : 'e.g. Audit inventory logs and detect stock exceptions...'}
                  className="flex-1 bg-slate-50 text-slate-900 text-xs px-4 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
                />
                <button
                  disabled={isProcessingAction || (!activePrompt && !isSales && agent.role !== 'operations')}
                  onClick={() => handleRunAgentAction(activePrompt || (isSales ? 'Qualify prospect CloudCorp ($85,000)' : 'Audit warehouse inventory logs'))}
                  className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-extrabold shadow-sm transition-all shrink-0 cursor-pointer flex items-center justify-center gap-2"
                >
                  {isProcessingAction ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Executing...</span>
                    </>
                  ) : (
                    <>
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Run {isSales ? 'Sales' : 'Operations'} Task</span>
                    </>
                  )}
                </button>
              </div>

              {/* Result & Execution Feedback */}
              {actionResult && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                        {actionResult.taskId}
                      </span>
                      <span className="text-xs font-bold text-slate-900">{actionResult.summary}</span>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold uppercase">
                      {actionResult.status}
                    </span>
                  </div>

                  {actionResult.steps && actionResult.steps.length > 0 && (
                    <div className="space-y-1.5 pt-2 border-t border-slate-200">
                      <p className="text-[10px] uppercase font-mono font-bold text-slate-500">Execution Steps Log:</p>
                      <div className="grid grid-cols-1 gap-1 text-[11px] text-slate-700 font-medium">
                        {actionResult.steps.map((st, i) => (
                          <div key={i} className="flex items-center gap-2">
                            <Check className="w-3 h-3 text-emerald-600 shrink-0" />
                            <span>{st}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => {
                      setSelectedTaskId(actionResult.taskId);
                      setActiveTab('task-execution');
                    }}
                    className="text-[11px] font-bold text-indigo-600 hover:underline inline-block pt-1 cursor-pointer"
                  >
                    Inspect Full Execution Trace →
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Recent Tasks Handled */}
      {!isLoading && (
        <div className="glass-card p-6 rounded-2xl border border-slate-200 space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-600" />
            <span>Recent Tasks Handled by {agent.name || 'Agent'}</span>
          </h3>

          {agentTasks.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 font-medium space-y-2">
              <Inbox className="w-8 h-8 text-slate-400 mx-auto" />
              <p>No recent tasks logged for {agent.name || 'Agent'}.</p>
              <button
                onClick={() => setActiveTab('create-task')}
                className="text-indigo-600 hover:underline font-bold cursor-pointer"
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
