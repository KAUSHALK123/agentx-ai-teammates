import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { 
  CheckCircle2, 
  X
} from 'lucide-react';

interface IntegrationCardItem {
  id: string;
  name: string;
  category: string;
  description: string;
  status: 'CONNECTED' | 'NOT CONNECTED';
  iconType: 'hubspot' | 'gmail' | 'slack' | 'n8n';
}

interface ActionToolRow {
  identifier: string;
  domain: string;
  accessType: 'READ-ONLY' | 'READ/WRITE';
  status: 'READY';
  availableTo: ('S' | 'G' | 'F')[];
}

export const IntegrationsView: React.FC = () => {
  const { integrations } = useApp();

  const [cards, setCards] = useState<IntegrationCardItem[]>([
    {
      id: 'hubspot',
      name: 'HubSpot CRM',
      category: 'CRM & PIPELINE',
      description: 'Lead lifecycle management and activity orchestration bridge.',
      status: 'CONNECTED',
      iconType: 'hubspot'
    },
    {
      id: 'gmail',
      name: 'Gmail (Enterprise)',
      category: 'COMMUNICATION',
      description: 'Secure external communication and outreach dispatch.',
      status: 'CONNECTED',
      iconType: 'gmail'
    },
    {
      id: 'slack',
      name: 'Slack Workspace',
      category: 'COLLABORATION',
      description: 'Internal notifications and collaborative human-in-loop escalations.',
      status: 'NOT CONNECTED',
      iconType: 'slack'
    },
    {
      id: 'n8n',
      name: 'n8n Orchestration',
      category: 'ORCHESTRATION',
      description: 'High-complexity multi-tool workflow and record logic bridge.',
      status: 'CONNECTED',
      iconType: 'n8n'
    }
  ]);

  const [configureModalItem, setConfigureModalItem] = useState<IntegrationCardItem | null>(null);

  // Default atomic action tools matching Reference Image 3 + dynamic tools
  const defaultTools: ActionToolRow[] = [
    {
      identifier: 'lookup_customer',
      domain: 'CRM / HubSpot',
      accessType: 'READ-ONLY',
      status: 'READY',
      availableTo: ['S', 'G', 'F']
    },
    {
      identifier: 'process_refund',
      domain: 'Finance / Stripe',
      accessType: 'READ/WRITE',
      status: 'READY',
      availableTo: ['S', 'F']
    },
    {
      identifier: 'n8n_process_lead',
      domain: 'Marketing / n8n',
      accessType: 'READ/WRITE',
      status: 'READY',
      availableTo: ['G']
    },
    {
      identifier: 'get_business_data',
      domain: 'Warehouse / PostgreSQL',
      accessType: 'READ-ONLY',
      status: 'READY',
      availableTo: ['F']
    },
    {
      identifier: 'verify_record',
      domain: 'Audit / ERP',
      accessType: 'READ-ONLY',
      status: 'READY',
      availableTo: ['F']
    },
    {
      identifier: 'n8n_operations_check',
      domain: 'Logistics / n8n',
      accessType: 'READ/WRITE',
      status: 'READY',
      availableTo: ['F']
    }
  ];

  // Dynamically augment with tools returned by backend if available
  const displayTools: ActionToolRow[] = integrations && integrations.length > 0
    ? [
        ...defaultTools,
        ...integrations
          .filter(it => !defaultTools.some(dt => dt.identifier === it.id))
          .map(it => ({
            identifier: it.id,
            domain: `${it.category} / ${it.name.split(' ')[0]}`,
            accessType: (it.permissionLevel === 'Approval Required' ? 'READ/WRITE' : 'READ-ONLY') as 'READ-ONLY' | 'READ/WRITE',
            status: 'READY' as const,
            availableTo: ['S', 'G', 'F'] as ('S' | 'G' | 'F')[]
          }))
      ]
    : defaultTools;

  const toggleConnect = (id: string) => {
    setCards(prev => prev.map(c => {
      if (c.id === id) {
        const nextStatus = c.status === 'CONNECTED' ? 'NOT CONNECTED' : 'CONNECTED';
        return { ...c, status: nextStatus };
      }
      return c;
    }));
  };

  const renderBrandLogo = (type: string) => {
    switch (type) {
      case 'hubspot':
        return (
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-orange-50 text-orange-600 font-extrabold text-base border border-orange-200">
            Hub<span className="text-orange-500">Spot</span>
          </div>
        );
      case 'gmail':
        return (
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-white shadow-xs border border-slate-200">
            <span className="font-extrabold text-red-500 text-lg">M</span>
          </div>
        );
      case 'slack':
        return (
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-slate-50 border border-slate-200 text-slate-700 font-extrabold text-lg">
            #
          </div>
        );
      case 'n8n':
        return (
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-pink-50 text-pink-600 font-extrabold text-base border border-pink-200">
            ☍
          </div>
        );
      default:
        return (
          <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-slate-100 text-slate-700 font-bold">
            API
          </div>
        );
    }
  };

  return (
    <div className="space-y-12 max-w-7xl mx-auto">
      {/* Header matching Reference Image 3 */}
      <div>
        <h1 className="text-4xl font-display font-extrabold text-slate-900 tracking-tight">
          Integrations & Tools
        </h1>
        <p className="text-slate-500 text-sm mt-2 font-normal">
          Connect AgentX to the enterprise tools your AI teammates use to get work done.
        </p>
      </div>

      {/* Top 4 Cards Grid matching Reference Image 3 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((card) => {
          const isConnected = card.status === 'CONNECTED';

          return (
            <div
              key={card.id}
              className="glass-card rounded-[32px] p-6 border border-white/70 shadow-lg hover:shadow-xl transition-all flex flex-col justify-between space-y-6 bg-white/80"
            >
              <div className="space-y-4">
                {/* Brand Logo & Status Pill */}
                <div className="flex items-center justify-between">
                  {renderBrandLogo(card.iconType)}

                  <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-mono font-bold tracking-wider ${
                    isConnected 
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' 
                      : 'bg-slate-100 text-slate-500 border border-slate-200'
                  }`}>
                    {card.status}
                  </span>
                </div>

                {/* Title & Description */}
                <div>
                  <h3 className="text-base font-display font-extrabold text-slate-900">
                    {card.name}
                  </h3>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed font-normal">
                    {card.description}
                  </p>
                </div>
              </div>

              {/* Action Button: Configure or Connect Account */}
              <div className="pt-2">
                {isConnected ? (
                  <button
                    onClick={() => setConfigureModalItem(card)}
                    className="w-full py-2.5 px-4 rounded-full bg-white hover:bg-slate-50 text-slate-800 text-xs font-bold border border-slate-200/80 shadow-xs hover:shadow-sm transition-all text-center cursor-pointer"
                  >
                    Configure
                  </button>
                ) : (
                  <button
                    onClick={() => toggleConnect(card.id)}
                    className="w-full py-2.5 px-4 rounded-full bg-cyan-500 hover:bg-cyan-600 text-white text-xs font-extrabold shadow-md shadow-cyan-500/25 transition-all text-center cursor-pointer"
                  >
                    Connect Account
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Atomic Action Tools Section matching Reference Image 3 */}
      <div className="space-y-6">
        <h2 className="text-2xl font-display font-extrabold text-slate-900 tracking-tight">
          Atomic Action Tools
        </h2>

        {/* Large Rounded Table */}
        <div className="glass-card rounded-[32px] p-8 border border-white/70 shadow-xl bg-white/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-[10px] font-mono uppercase tracking-wider text-slate-400 border-b border-slate-100 pb-4">
                  <th className="font-bold py-4 pr-6">TOOL IDENTIFIER</th>
                  <th className="font-bold py-4 px-6">DOMAIN</th>
                  <th className="font-bold py-4 px-6">ACCESS TYPE</th>
                  <th className="font-bold py-4 px-6">AUTHORIZATION STATUS</th>
                  <th className="font-bold py-4 pl-6 text-right">AVAILABLE TO</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100/80 text-xs">
                {displayTools.map((tool, idx) => {
                  const isReadWrite = tool.accessType === 'READ/WRITE';

                  return (
                    <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                      {/* Tool Identifier */}
                      <td className="py-5 pr-6 font-mono font-bold text-slate-900">
                        {tool.identifier}
                      </td>

                      {/* Domain */}
                      <td className="py-5 px-6 font-medium text-slate-600">
                        {tool.domain}
                      </td>

                      {/* Access Type (Pill / boxed) */}
                      <td className="py-5 px-6">
                        <span className={`inline-block px-3 py-1 rounded-md text-[10px] font-mono font-bold uppercase tracking-wider border ${
                          isReadWrite
                            ? 'border-amber-300 text-amber-600 bg-amber-50/30'
                            : 'border-slate-200 text-slate-600 bg-slate-50'
                        }`}>
                          {tool.accessType}
                        </span>
                      </td>

                      {/* Authorization Status */}
                      <td className="py-5 px-6">
                        <div className="flex items-center gap-1.5 text-[11px] font-mono font-bold text-slate-800">
                          <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                          <span className="tracking-wider">READY</span>
                        </div>
                      </td>

                      {/* Available To Chips */}
                      <td className="py-5 pl-6">
                        <div className="flex items-center justify-end gap-1.5">
                          {tool.availableTo.includes('S') && (
                            <span 
                              className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-[10px] font-extrabold flex items-center justify-center shadow-2xs"
                              title="Support Lead"
                            >
                              S
                            </span>
                          )}
                          {tool.availableTo.includes('G') && (
                            <span 
                              className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-extrabold flex items-center justify-center shadow-2xs"
                              title="Growth Engine"
                            >
                              G
                            </span>
                          )}
                          {tool.availableTo.includes('F') && (
                            <span 
                              className="w-5 h-5 rounded-full bg-amber-100 text-amber-800 text-[10px] font-extrabold flex items-center justify-center shadow-2xs"
                              title="Flow Architect"
                            >
                              F
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Configuration Modal */}
      {configureModalItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-[32px] p-8 max-w-md w-full shadow-2xl border border-slate-100 space-y-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <div className="flex items-center gap-3">
                {renderBrandLogo(configureModalItem.iconType)}
                <div>
                  <h3 className="text-base font-bold text-slate-900">{configureModalItem.name}</h3>
                  <p className="text-xs text-slate-500">{configureModalItem.category}</p>
                </div>
              </div>
              <button
                onClick={() => setConfigureModalItem(null)}
                className="p-1.5 rounded-full hover:bg-slate-100 text-slate-400 hover:text-slate-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-600 font-bold mb-1">API Endpoint / Webhook Target</label>
                <input
                  type="text"
                  readOnly
                  value={`https://api.${configureModalItem.id}.internal/v2/events`}
                  className="w-full bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-slate-700 font-mono"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-bold mb-1">Permission Level</label>
                <select className="w-full bg-slate-50 p-2.5 rounded-xl border border-slate-200 text-slate-800 font-medium">
                  <option>Full Autonomy with Guardrails</option>
                  <option>Approval Required on Write Operations</option>
                  <option>Read Only</option>
                </select>
              </div>

              <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-800 flex items-center gap-2 font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span>Encrypted OAuth2 session active. Handshake verified.</span>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={() => {
                  toggleConnect(configureModalItem.id);
                  setConfigureModalItem(null);
                }}
                className="flex-1 py-2.5 rounded-full bg-red-50 hover:bg-red-100 text-red-700 text-xs font-bold border border-red-200 transition-colors text-center cursor-pointer"
              >
                Disconnect
              </button>
              <button
                onClick={() => setConfigureModalItem(null)}
                className="flex-1 py-2.5 rounded-full bg-cyan-500 hover:bg-cyan-600 text-white text-xs font-extrabold shadow-md shadow-cyan-500/25 transition-colors text-center cursor-pointer"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default IntegrationsView;
