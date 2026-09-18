import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  Settings, 
  Building2, 
  Bot, 
  ShieldCheck, 
  Wrench, 
  Bell, 
  Key, 
  User, 
  Save
} from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { workspace, setWorkspace } = useApp();

  const [activeSubTab, setActiveSubTab] = useState<'workspace' | 'agents' | 'approvals' | 'tools' | 'notifications' | 'api' | 'account'>('workspace');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const [autoApproveLimit, setAutoApproveLimit] = useState(200);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [slackWebhook, setSlackWebhook] = useState('https://hooks.slack.com/services/T00/B00/XXXX');
  const [mcpEndpoint, setMcpEndpoint] = useState('http://localhost:8000/mcp/v1');

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 text-[11px] font-mono font-bold mb-2">
            <Settings className="w-3.5 h-3.5 text-indigo-600" />
            <span>PLATFORM CONFIGURATION</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">Workspace Settings</h2>
          <p className="text-xs text-slate-500 font-medium">
            Configure agent personas, human approval thresholds, tool permissions, and integration keys.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
        >
          <Save className="w-4 h-4" />
          <span>{savedSuccess ? 'Saved Changes!' : 'Save Settings'}</span>
        </button>
      </div>

      <div className="flex items-center gap-1 bg-slate-100 p-1.5 rounded-2xl border border-slate-200 overflow-x-auto">
        {[
          { id: 'workspace', label: 'Workspace', icon: <Building2 className="w-3.5 h-3.5" /> },
          { id: 'agents', label: 'Agent Configuration', icon: <Bot className="w-3.5 h-3.5" /> },
          { id: 'approvals', label: 'Approval Policies', icon: <ShieldCheck className="w-3.5 h-3.5" /> },
          { id: 'tools', label: 'Tool Permissions', icon: <Wrench className="w-3.5 h-3.5" /> },
          { id: 'notifications', label: 'Notifications', icon: <Bell className="w-3.5 h-3.5" /> },
          { id: 'api', label: 'API & MCP Keys', icon: <Key className="w-3.5 h-3.5" /> },
          { id: 'account', label: 'Account & Team', icon: <User className="w-3.5 h-3.5" /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveSubTab(tab.id as any)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              activeSubTab === tab.id
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
            }`}
          >
            {tab.icon}
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="glass-card p-6 md:p-8 rounded-2xl border border-slate-200 space-y-6">
        {activeSubTab === 'workspace' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">Workspace General Settings</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">Workspace Name</label>
                <input
                  type="text"
                  value={workspace}
                  onChange={(e) => setWorkspace(e.target.value)}
                  className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">Region / Data Center</label>
                <select className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-medium">
                  <option>US-East (N. Virginia - Low Latency)</option>
                  <option>EU-Central (Frankfurt)</option>
                  <option>AP-South (Mumbai)</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'agents' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">AI Teammate Persona & Execution Limits</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">Max Task Execution Steps</label>
                <input
                  type="number"
                  defaultValue={10}
                  className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 max-w-xs font-medium"
                />
                <p className="text-[10px] text-slate-500 mt-1">Prevents infinite tool execution loops.</p>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">System Persona Instruction Guardrail</label>
                <textarea
                  rows={3}
                  defaultValue="Always verify customer VIP status before calculating store credit. Never execute financial transactions exceeding auto-approve limit without human signoff."
                  className="w-full bg-slate-50 text-slate-900 text-xs p-3 rounded-xl border border-slate-200 leading-relaxed font-medium"
                ></textarea>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'approvals' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">Human-in-the-Loop Approval Policies</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">
                  Auto-Approve Refund Limit ($ USD)
                </label>
                <input
                  type="number"
                  value={autoApproveLimit}
                  onChange={(e) => setAutoApproveLimit(Number(e.target.value))}
                  className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 max-w-xs font-medium"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Refunds above ${autoApproveLimit} require explicit human approval.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-800">Require Approval for External Emails</span>
                  <input type="checkbox" defaultChecked className="w-4 h-4 accent-indigo-600 rounded" />
                </div>
                <p className="text-[11px] text-slate-500">
                  When enabled, outbound sales/support emails to non-internal recipients trigger a Human Approval request.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'tools' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">Tool & API Permissions Matrix</h3>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="font-medium text-slate-800">Shopify / ERP Order Lookup</span>
                <span className="text-emerald-700 font-mono font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Full Autonomy (Read)</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="font-medium text-slate-800">Stripe Refund Gateway</span>
                <span className="text-amber-700 font-mono font-bold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">Approval Required (&gt;$200)</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200">
                <span className="font-medium text-slate-800">n8n Purchase Order Webhook</span>
                <span className="text-emerald-700 font-mono font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">Full Autonomy</span>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'notifications' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">Notifications & Alerting</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">Slack Webhook URL</label>
                <input
                  type="text"
                  value={slackWebhook}
                  onChange={(e) => setSlackWebhook(e.target.value)}
                  className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-medium"
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                  className="w-4 h-4 accent-indigo-600 rounded"
                />
                <span className="text-xs text-slate-700 font-medium">Send email notification when a task requires human approval</span>
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'api' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">API Keys & MCP Server Settings</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">AgentX Core API Key</label>
                <input
                  type="password"
                  defaultValue="agx_live_99481029481928"
                  className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-600 font-bold mb-1">MCP (Model Context Protocol) Endpoint</label>
                <input
                  type="text"
                  value={mcpEndpoint}
                  onChange={(e) => setMcpEndpoint(e.target.value)}
                  className="w-full bg-slate-50 text-slate-900 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 font-mono"
                />
              </div>
            </div>
          </div>
        )}

        {activeSubTab === 'account' && (
          <div className="space-y-4">
            <h3 className="text-base font-bold text-slate-900">Account Profile & Team Seats</h3>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <p className="text-xs font-bold text-slate-900">Operator Admin (Head of Operations)</p>
              <p className="text-xs text-slate-500 font-medium">admin@acme.com • Enterprise Plan (Unlimited AI Teammates)</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
