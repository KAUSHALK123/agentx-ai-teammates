import React from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Workflow, 
  Server, 
  Briefcase, 
  ShieldCheck, 
  Plus
} from 'lucide-react';

export const IntegrationsView: React.FC = () => {
  const { integrations } = useApp();

  return (
    <div className="p-6 md:p-8 space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <Workflow className="w-3.5 h-3.5 text-indigo-600" />
            <span>CONNECTED TOOL ECOSYSTEM</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Integrations & Tool Registry</h2>
          <p className="text-xs text-slate-500 font-medium">
            Configure external tool connections, n8n workflow scenarios, MCP protocol servers, and guardrail permission levels.
          </p>
        </div>

        <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all">
          <Plus className="w-4 h-4" />
          <span>Connect New System / API</span>
        </button>
      </div>

      <div className="glass-card p-6 md:p-8 rounded-2xl border-2 border-purple-200 bg-gradient-to-r from-purple-50/80 via-white to-indigo-50/80 relative overflow-hidden shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 z-10">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full font-mono text-[10px] bg-purple-100 text-purple-800 border border-purple-200 font-bold">
                n8n WORKFLOW ENGINE + MCP PROTOCOL
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                ACTIVE
              </span>
            </div>
            <h3 className="text-xl font-extrabold text-slate-900">Native n8n & Model Context Protocol Orchestration</h3>
            <p className="text-xs text-slate-600 max-w-2xl leading-relaxed font-medium">
              AgentX triggers complex n8n node automation flows (e.g. ERP Purchase Orders, Slack Alerts) and communicates via MCP endpoints with full sandbox permission verification.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-white border border-purple-200 text-purple-700 text-center font-mono shadow-xs">
              <Workflow className="w-6 h-6 mx-auto mb-1 text-purple-600" />
              <p className="text-[10px] font-bold">n8n Flows</p>
            </div>
            <div className="p-3 rounded-xl bg-white border border-indigo-200 text-indigo-700 text-center font-mono shadow-xs">
              <Server className="w-6 h-6 mx-auto mb-1 text-indigo-600" />
              <p className="text-[10px] font-bold">MCP Server</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.map((item) => (
          <div
            key={item.id}
            className={`glass-card rounded-2xl p-6 border transition-all flex flex-col justify-between space-y-6 ${
              item.isN8n ? 'border-purple-200 bg-purple-50/20 hover:border-purple-300' :
              item.isMCP ? 'border-indigo-200 bg-indigo-50/20 hover:border-indigo-300' :
              'border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-center text-indigo-600">
                    {item.isN8n ? <Workflow className="w-5 h-5 text-purple-600" /> :
                     item.isMCP ? <Server className="w-5 h-5 text-indigo-600" /> :
                     <Briefcase className="w-5 h-5 text-blue-600" />}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{item.name}</h4>
                    <p className="text-[10px] text-slate-500 font-medium">{item.category}</p>
                  </div>
                </div>

                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                  {item.status}
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed font-medium">
                {item.description}
              </p>

              <div className="space-y-2">
                <p className="text-[10px] uppercase font-mono text-slate-500 font-bold">
                  Exposed Tool Functions ({item.availableTools.length})
                </p>
                <div className="space-y-1.5">
                  {item.availableTools.map((t, idx) => (
                    <div
                      key={idx}
                      className="px-2.5 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-700 flex items-center justify-between font-medium"
                    >
                      <span>{t}</span>
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[10px] font-mono text-slate-500 font-medium">Guardrail Permission:</span>
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                item.permissionLevel === 'Full Autonomy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                item.permissionLevel === 'Approval Required' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                'bg-slate-100 text-slate-700 border border-slate-200'
              }`}>
                {item.permissionLevel}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
