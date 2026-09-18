import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Headphones, 
  BarChart3, 
  Workflow
} from 'lucide-react';
import type { AgentRole } from '../../types';

export const AgentsView: React.FC = () => {
  const { agents, tasks, setSelectedAgentRole, setActiveTab } = useApp();

  const handleOpenAgent = (role: AgentRole) => {
    setSelectedAgentRole(role);
    setActiveTab('agent-detail');
  };

  const handleStartTask = (role: AgentRole) => {
    setSelectedAgentRole(role);
    setActiveTab('create-task');
  };

  // Agent configs matching Image 1 exactly with dynamic task and context bindings
  const supportTasksCount = agents?.support?.tasksCompleted || (tasks || []).filter(t => t.agentRole === 'support').length || 89;
  const salesTasksCount = agents?.sales?.tasksCompleted || (tasks || []).filter(t => t.agentRole === 'sales').length || 34;
  const opsTasksCount = agents?.operations?.tasksCompleted || (tasks || []).filter(t => t.agentRole === 'operations').length || 142;

  const supportAccuracy = agents?.support?.successRate ? `${agents.support.successRate}%` : '96%';
  const salesAccuracy = agents?.sales?.successRate ? `${agents.sales.successRate}%` : '92%';
  const opsAccuracy = agents?.operations?.successRate ? `${agents.operations.successRate}%` : '98.9%';

  const agentCards = [
    {
      role: 'support' as AgentRole,
      name: 'Support Lead',
      subtitle: 'Customer Resolution Specialist',
      status: 'ONLINE',
      statusColor: 'text-emerald-500',
      dotColor: 'bg-emerald-500',
      iconBg: 'bg-[#2563eb]',
      Icon: Headphones,
      description: 'Handles customer complaints, order issues, payment disputes, and escalation logic.',
      tools: [
        { name: 'Zendesk', icon: 'Z', bg: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
        { name: 'Gmail', icon: 'M', bg: 'bg-red-50 text-red-600 border-red-200' },
        { name: 'Shopify', icon: '🛍️', bg: 'bg-slate-50 text-slate-700 border-slate-200' }
      ],
      tasksDone: supportTasksCount,
      accuracy: supportAccuracy
    },
    {
      role: 'sales' as AgentRole,
      name: 'Growth Engine',
      subtitle: 'Commercial Account & Lead Specialist',
      status: 'EXECUTING',
      statusColor: 'text-cyan-500',
      dotColor: 'bg-cyan-500',
      iconBg: 'bg-[#10b981]',
      Icon: BarChart3,
      description: 'Lead qualification, follow-ups, sales CRM management, and lead scoring.',
      tools: [
        { name: 'HubSpot', icon: '🟠', bg: 'bg-orange-50 text-orange-600 border-orange-200' },
        { name: 'LinkedIn', icon: 'in', bg: 'bg-blue-50 text-blue-700 border-blue-200' },
        { name: 'Slack', icon: '#', bg: 'bg-purple-50 text-purple-700 border-purple-200' }
      ],
      tasksDone: salesTasksCount,
      accuracy: salesAccuracy
    },
    {
      role: 'operations' as AgentRole,
      name: 'Flow Architect',
      subtitle: 'Logistics & Workflow Specialist',
      status: 'ACTIVE',
      statusColor: 'text-emerald-500',
      dotColor: 'bg-emerald-500',
      iconBg: 'bg-[#f59e0b]',
      Icon: Workflow,
      description: 'Data reporting, record verification, and synchronization across back-office systems.',
      tools: [
        { name: 'Stripe', icon: 'S', bg: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
        { name: 'PostgreSQL', icon: '🐘', bg: 'bg-blue-50 text-blue-800 border-blue-200' },
        { name: 'n8n', icon: '☍', bg: 'bg-pink-50 text-pink-600 border-pink-200' }
      ],
      tasksDone: opsTasksCount,
      accuracy: opsAccuracy
    }
  ];

  return (
    <div className="space-y-10 max-w-7xl mx-auto">
      {/* Header matching Reference Image 1 */}
      <div>
        <h1 className="text-4xl font-display font-extrabold text-slate-900 tracking-tight">
          AI Teammates
        </h1>
        <p className="text-slate-500 text-sm mt-2 font-normal">
          Specialized autonomous agents orchestrating your business stack.
        </p>
      </div>

      {/* 3 Large Agent Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {agentCards.map((agent) => {
          const IconComponent = agent.Icon;

          return (
            <div
              key={agent.role}
              className="glass-card rounded-[36px] p-8 border border-white/70 shadow-xl hover:shadow-2xl transition-all flex flex-col justify-between space-y-8 relative overflow-hidden bg-white/80"
            >
              <div className="space-y-6">
                {/* Agent Icon (Square with rounded corners) */}
                <div className={`w-14 h-14 ${agent.iconBg} rounded-[20px] flex items-center justify-center text-white shadow-lg`}>
                  <IconComponent className="w-7 h-7" />
                </div>

                {/* Status Indicator */}
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${agent.dotColor}`}></span>
                  <span className={`text-[11px] font-mono font-bold tracking-wider ${agent.statusColor}`}>
                    {agent.status}
                  </span>
                </div>

                {/* Agent Title & Description */}
                <div>
                  <h2 className="text-2xl font-display font-extrabold text-slate-900">
                    {agent.name}
                  </h2>
                  <p className="text-xs text-slate-500 mt-2.5 leading-relaxed font-normal">
                    {agent.description}
                  </p>
                </div>

                {/* Tool Icon Chips */}
                <div className="flex items-center gap-2.5 pt-1">
                  {agent.tools.map((tool, idx) => (
                    <div
                      key={idx}
                      className={`w-8 h-8 rounded-xl border flex items-center justify-center text-xs font-bold shadow-xs ${tool.bg}`}
                      title={tool.name}
                    >
                      {tool.icon}
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom Metrics & Actions */}
              <div className="space-y-6 pt-4 border-t border-slate-100">
                {/* Metrics Row */}
                <div className="flex items-center justify-between text-xs">
                  <div className="space-y-1">
                    <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                      TASKS DONE
                    </p>
                    <p className="text-sm font-display font-extrabold text-slate-900">
                      {agent.tasksDone}
                    </p>
                  </div>

                  <div className="space-y-1 text-right">
                    <p className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold">
                      ACCURACY
                    </p>
                    <p className="text-sm font-display font-extrabold text-emerald-600">
                      {agent.accuracy}
                    </p>
                  </div>
                </div>

                {/* Pill Buttons: Open Agent & Start Task */}
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleOpenAgent(agent.role)}
                    className="flex-1 py-3 px-5 rounded-full bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold border border-slate-200/80 shadow-xs hover:shadow-sm transition-all text-center cursor-pointer"
                  >
                    Open Agent
                  </button>
                  <button
                    onClick={() => handleStartTask(agent.role)}
                    className="flex-1 py-3 px-5 rounded-full bg-cyan-500 hover:bg-cyan-600 text-white text-xs font-extrabold shadow-md shadow-cyan-500/25 hover:shadow-lg transition-all text-center cursor-pointer"
                  >
                    Start Task
                  </button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default AgentsView;
