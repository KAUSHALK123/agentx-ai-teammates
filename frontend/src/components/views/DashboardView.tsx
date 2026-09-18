import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Zap, 
  CheckCircle, 
  ShieldCheck, 
  Layers, 
  Headphones, 
  BarChart3, 
  Settings2, 
  ChevronRight, 
  Bot, 
  User, 
  Mic, 
  Send, 
  AlertCircle, 
  Mail, 
  MoreHorizontal
} from 'lucide-react';
import type { AgentRole } from '../../types';

export const DashboardView: React.FC = () => {
  const { 
    setActiveTab, 
    setSelectedAgentRole, 
    setSelectedTaskId, 
    tasks, 
    agents, 
    integrations, 
    analytics, 
    createNewTask 
  } = useApp();

  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'ai' | 'user'; text: string; buttons?: string[] }>>([
    {
      sender: 'ai',
      text: "Good morning. AgentX workforce is online. You can type instructions or customer inquiries to dispatch autonomous tasks."
    }
  ]);

  const [inputPrompt, setInputPrompt] = useState('');
  const [isRecording, setIsRecording] = useState(false);

  const activeCount = tasks.filter(t => t.status === 'EXECUTING' || t.status === 'WAITING_FOR_APPROVAL').length;
  const completedCount = tasks.filter(t => t.status === 'COMPLETED').length;

  const handleSendPrompt = (textToSend?: string) => {
    const prompt = textToSend || inputPrompt;
    if (!prompt.trim()) return;

    // Add user message
    setChatMessages(prev => [...prev, { sender: 'user', text: prompt }]);
    setInputPrompt('');

    // Trigger AI response & dispatch task
    setTimeout(() => {
      createNewTask({
        title: prompt,
        description: prompt,
        agentRole: 'auto',
        priority: 'HIGH'
      });

      setChatMessages(prev => [
        ...prev,
        {
          sender: 'ai',
          text: `Task dispatched to AI workforce: "${prompt}". You can view execution timeline in real-time.`
        }
      ]);
    }, 800);
  };

  const navigateToAgentDetail = (role: AgentRole) => {
    setSelectedAgentRole(role);
    setActiveTab('agent-detail');
  };

  return (
    <div className="space-y-10">
      {/* Workspace Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-4xl font-display font-bold text-slate-900">Workspace Pulse</h1>
          <p className="text-slate-500 mt-2 text-lg">
            Orchestrating <span className="text-cyan-600 font-bold italic">3 autonomous agents</span> across {integrations.length} enterprise tools.
          </p>
        </div>
        <div className="flex gap-3">
          <button 
            onClick={() => setActiveTab('analytics')}
            className="px-4 py-2 glass-card rounded-xl text-sm font-bold text-slate-600 hover:bg-white/60 transition-colors shadow-xs"
          >
            Daily Report
          </button>
          <button 
            onClick={() => setActiveTab('agents')}
            className="px-4 py-2 glass-card rounded-xl text-sm font-bold text-slate-600 hover:bg-white/60 transition-colors shadow-xs"
          >
            Agent Health
          </button>
        </div>
      </div>

      {/* Main 12-Column Grid */}
      <div className="grid grid-cols-12 gap-8">
        {/* Metric Column (2 Cols) */}
        <div className="col-span-12 lg:col-span-2 space-y-4">
          <div className="glass-card p-5 rounded-2xl">
            <div className="p-2.5 bg-cyan-100/50 text-cyan-600 rounded-xl w-fit mb-3">
              <Zap className="w-5 h-5" />
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Active</p>
            <h3 className="text-xl font-display font-bold text-slate-900 mt-1">{activeCount.toString().padStart(2, '0')}</h3>
          </div>

          <div className="glass-card p-5 rounded-2xl">
            <div className="p-2.5 bg-green-100/50 text-green-600 rounded-xl w-fit mb-3">
              <CheckCircle className="w-5 h-5" />
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Done</p>
            <h3 className="text-xl font-display font-bold text-slate-900 mt-1">{completedCount.toString().padStart(2, '0')}</h3>
          </div>

          <div className="glass-card p-5 rounded-2xl">
            <div className="p-2.5 bg-blue-100/50 text-blue-600 rounded-xl w-fit mb-3">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Rate</p>
            <h3 className="text-xl font-display font-bold text-slate-900 mt-1">{analytics.successRate}%</h3>
          </div>

          <div className="glass-card p-5 rounded-2xl">
            <div className="p-2.5 bg-purple-100/50 text-purple-600 rounded-xl w-fit mb-3">
              <Layers className="w-5 h-5" />
            </div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tools</p>
            <h3 className="text-xl font-display font-bold text-slate-900 mt-1">{integrations.length.toString().padStart(2, '0')}</h3>
          </div>
        </div>

        {/* AI Teammates Column (4 Cols) */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          {/* Support Lead Card */}
          <div className="glass-card p-6 rounded-[32px] hover:shadow-xl transition-all relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 w-24 h-24 bg-cyan-100/30 rounded-full blur-2xl"></div>
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-blue-500 text-white rounded-[16px] flex items-center justify-center shadow-md">
                <Headphones className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{agents['support']?.status || 'Standby'}</span>
            </div>
            <h4 className="text-lg font-display font-bold text-slate-900 mb-1">{agents['support']?.name || 'Support Lead'}</h4>
            <div className="flex gap-2 mb-4">
              <div className="tool-chip px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-slate-600">Zendesk</div>
              <div className="tool-chip px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-slate-600">Gmail</div>
            </div>
            <button 
              onClick={() => navigateToAgentDetail('support')}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/60 text-slate-700 rounded-xl text-xs font-bold hover:bg-white transition-all shadow-xs"
            >
              <span>Details</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Growth Engine Card */}
          <div className="glass-card p-6 rounded-[32px] hover:shadow-xl transition-all relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 w-24 h-24 bg-emerald-100/30 rounded-full blur-2xl"></div>
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-cyan-500 text-white rounded-[16px] flex items-center justify-center shadow-md">
                <BarChart3 className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-bold text-cyan-600 uppercase tracking-widest flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping"></span>
                {agents['sales']?.status || 'Executing'}
              </span>
            </div>
            <h4 className="text-lg font-display font-bold text-slate-900 mb-1">{agents['sales']?.name || 'Growth Engine'}</h4>
            <div className="flex gap-2 mb-4">
              <div className="tool-chip px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-slate-600">HubSpot</div>
              <div className="tool-chip px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-slate-600">LinkedIn</div>
            </div>
            <button 
              onClick={() => navigateToAgentDetail('sales')}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/60 text-slate-700 rounded-xl text-xs font-bold hover:bg-white transition-all shadow-xs"
            >
              <span>Details</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Flow Architect Card */}
          <div className="glass-card p-6 rounded-[32px] hover:shadow-xl transition-all relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 w-24 h-24 bg-amber-100/30 rounded-full blur-2xl"></div>
            <div className="flex justify-between items-start mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 text-white rounded-[16px] flex items-center justify-center shadow-md">
                <Settings2 className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{agents['operations']?.status || 'Active'}</span>
            </div>
            <h4 className="text-lg font-display font-bold text-slate-900 mb-1">{agents['operations']?.name || 'Flow Architect'}</h4>
            <div className="flex gap-2 mb-4">
              <div className="tool-chip px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-slate-600">Stripe</div>
              <div className="tool-chip px-2.5 py-1 rounded-lg text-xs font-mono font-bold text-slate-600">PostgreSQL</div>
            </div>
            <button 
              onClick={() => navigateToAgentDetail('operations')}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-white/60 text-slate-700 rounded-xl text-xs font-bold hover:bg-white transition-all shadow-xs"
            >
              <span>Details</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Command Center Chat Panel (6 Cols) */}
        <div className="col-span-12 lg:col-span-6 flex flex-col glass-card rounded-[40px] overflow-hidden min-h-[600px] border-white/60 shadow-2xl">
          {/* Chat Header */}
          <div className="p-6 border-b border-white/50 flex items-center gap-4 bg-white/20">
            <div className="relative w-14 h-14 bg-cyan-500 rounded-[20px] shadow-lg shadow-cyan-500/20 flex items-center justify-center overflow-hidden shrink-0">
              <div className="absolute inset-0 bg-gradient-to-tr from-cyan-600 to-cyan-400"></div>
              <div className="relative flex flex-col items-center gap-1">
                <div className="flex gap-1.5">
                  <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                  <div className="w-1.5 h-1.5 bg-white rounded-full"></div>
                </div>
                <div className="w-5 h-1 bg-white/40 rounded-full"></div>
              </div>
            </div>
            <div>
              <h3 className="text-xl font-display font-bold text-slate-900">AgentX Command Center</h3>
              <div className="flex items-center gap-2 mt-0.5">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-ping"></div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Ready for instructions</span>
              </div>
            </div>
            <button className="ml-auto text-slate-400 hover:text-slate-600 transition-colors">
              <MoreHorizontal className="w-6 h-6" />
            </button>
          </div>

          {/* Chat Body */}
          <div className="flex-1 p-8 overflow-y-auto space-y-6 custom-scrollbar bg-white/5">
            {chatMessages.map((msg, idx) => (
              <div key={idx} className={`flex gap-4 ${msg.sender === 'user' ? 'flex-row-reverse' : 'max-w-[85%]'}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                  msg.sender === 'ai' ? 'bg-cyan-500 text-white' : 'bg-slate-200 text-slate-600'
                }`}>
                  {msg.sender === 'ai' ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
                </div>

                <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.sender === 'ai' 
                    ? 'glass-card text-slate-700 rounded-tl-none' 
                    : 'bg-cyan-500 text-white rounded-tr-none shadow-md'
                }`}>
                  <p>{msg.text}</p>

                  {msg.buttons && (
                    <div className="mt-4 grid grid-cols-2 gap-2">
                      {msg.buttons.map((btnLabel, i) => (
                        <button
                          key={i}
                          onClick={() => handleSendPrompt(`Assign to ${btnLabel}`)}
                          className="py-2 px-3 bg-white/80 border border-slate-200 text-[11px] font-bold text-slate-700 rounded-xl hover:bg-cyan-500 hover:text-white transition-all shadow-xs"
                        >
                          {btnLabel}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input Bar */}
          <div className="p-6 bg-white/40 border-t border-white/50">
            <div className="relative flex items-center">
              <input
                type="text"
                value={inputPrompt}
                onChange={(e) => setInputPrompt(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendPrompt()}
                placeholder="Tell me what you need done..."
                className="w-full pl-6 pr-24 py-4 bg-white border border-slate-200 rounded-2xl text-sm focus:outline-none focus:ring-4 focus:ring-cyan-500/10 transition-all font-medium text-slate-800"
              />
              <div className="absolute right-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setIsRecording(!isRecording)}
                  className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                    isRecording ? 'bg-red-100 text-red-600 animate-pulse' : 'text-slate-400 hover:text-cyan-500 hover:bg-cyan-50'
                  }`}
                  title="Voice Input"
                >
                  <Mic className="w-5 h-5" />
                </button>

                <button
                  type="button"
                  onClick={() => handleSendPrompt()}
                  className="w-10 h-10 bg-cyan-500 text-white rounded-xl shadow-lg shadow-cyan-500/20 flex items-center justify-center hover:bg-cyan-600 transition-all hover:scale-105"
                  title="Dispatch Instruction"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Live Task Stream & Recent Events */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Live Task Stream (3 Cols) */}
        <div className="lg:col-span-3 glass-card rounded-[40px] overflow-hidden shadow-sm">
          <div className="p-8 border-b border-white/50 flex justify-between items-center">
            <h3 className="text-xl font-display font-bold text-slate-800">Live Task Stream</h3>
            <button
              onClick={() => setActiveTab('task-history')}
              className="text-cyan-600 text-xs font-bold uppercase tracking-widest hover:text-cyan-700 transition-colors"
            >
              View Full Log
            </button>
          </div>

          <div className="divide-y divide-white/50">
            {tasks.slice(0, 2).map((t) => {
              const isWaiting = t.status === 'WAITING_FOR_APPROVAL';
              return (
                <div 
                  key={t.id}
                  onClick={() => {
                    setSelectedTaskId(t.id);
                    setActiveTab(isWaiting ? 'approvals' : 'task-execution');
                  }}
                  className="p-8 hover:bg-white/40 transition-all cursor-pointer group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      {isWaiting ? (
                        <AlertCircle className="w-5 h-5 text-orange-500" />
                      ) : (
                        <div className="w-3 h-3 bg-cyan-500 rounded-full shadow-[0_0_10px_#06B6D4] animate-pulse"></div>
                      )}
                      <span className="font-bold text-slate-900 group-hover:text-cyan-600 transition-colors">
                        {t.title}
                      </span>
                    </div>
                    <span className={`px-3 py-1 text-[10px] font-bold rounded-lg uppercase tracking-widest ${
                      isWaiting 
                        ? 'bg-orange-100 text-orange-600 animate-pulse' 
                        : t.status === 'COMPLETED'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-cyan-100 text-cyan-600'
                    }`}>
                      {isWaiting ? 'Human Awaited' : t.status}
                    </span>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-[10px] font-bold text-slate-400 uppercase">{t.agentName} • {t.id}</span>
                        <span className="text-[10px] font-mono text-cyan-600 font-bold">{t.status === 'COMPLETED' ? '100%' : '65%'}</span>
                      </div>
                      <div className="w-full h-2 bg-white/50 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-cyan-500 shadow-[0_0_8px_#06B6D4] transition-all duration-1000"
                          style={{ width: t.status === 'COMPLETED' ? '100%' : '65%' }}
                        ></div>
                      </div>
                    </div>
                    <div className="text-xs font-mono text-slate-400 font-bold">{t.createdAt}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Recent Events Column (2 Cols) */}
        <div className="lg:col-span-2 glass-card rounded-[40px] flex flex-col shadow-sm">
          <div className="p-8 border-b border-white/50">
            <h3 className="text-xl font-display font-bold text-slate-800">Recent Events</h3>
          </div>

          <div className="p-8 space-y-8 flex-1 overflow-y-auto custom-scrollbar">
            <div className="flex gap-5">
              <div className="w-12 h-12 rounded-2xl bg-green-500/10 text-green-600 flex items-center justify-center shrink-0 border border-green-500/20 shadow-xs">
                <CheckCircle className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm text-slate-800 leading-tight font-medium">
                  Refund sync successful for #TX-9902 via <span className="font-bold">Stripe Gateway</span>.
                </p>
                <span className="text-[10px] text-slate-400 font-bold uppercase mt-2 block">12 min ago</span>
              </div>
            </div>

            <div className="flex gap-5">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 text-cyan-600 flex items-center justify-center shrink-0 border border-cyan-500/20 shadow-xs">
                <Mail className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm text-slate-800 leading-tight font-medium">
                  Campaign triggered for 42 prospects in <span className="font-bold">HubSpot Sales</span>.
                </p>
                <span className="text-[10px] text-slate-400 font-bold uppercase mt-2 block">45 min ago</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
