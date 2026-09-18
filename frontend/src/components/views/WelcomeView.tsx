import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ThreeCoreCanvas } from '../ui/ThreeCoreCanvas';
import { 
  Sparkles, 
  ArrowRight, 
  ShieldCheck, 
  Workflow, 
  Zap, 
  Play, 
  UserCheck,
  Building2,
  Key
} from 'lucide-react';

export const WelcomeView: React.FC = () => {
  const { setActiveTab } = useApp();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [email, setEmail] = useState('operator@acme.com');

  return (
    <div className="min-h-full p-8 md:p-12 flex flex-col justify-between relative overflow-hidden bg-slate-50">
      {/* Subtle background gradient glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-indigo-200/40 blur-[120px] rounded-full pointer-events-none"></div>

      {/* Navigation Header */}
      <div className="flex items-center justify-between z-10 max-w-6xl mx-auto w-full mb-8">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold tracking-tight text-slate-900 flex items-center gap-2">
              Agent<span className="text-indigo-600">X</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono font-bold">
                ENTERPRISE
              </span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowLoginModal(true)}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:text-slate-900 hover:bg-slate-200/60 transition-colors"
          >
            Sign In
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition-all hover:scale-105"
          >
            <span>Launch Platform</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Hero Section */}
      <div className="max-w-5xl mx-auto text-center z-10 my-4 space-y-6">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-bold shadow-xs">
          <Zap className="w-3.5 h-3.5 text-indigo-600" />
          <span>Next-Generation AI Workforce Platform</span>
        </div>

        <h2 className="text-4xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
          Autonomous AI Teammates <br />
          <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-800 bg-clip-text text-transparent">
            Built for Business Execution
          </span>
        </h2>

        {/* 3D Interactive Canvas */}
        <div className="my-2 relative flex items-center justify-center">
          <div className="w-72 h-72 md:w-80 md:h-80 mx-auto pointer-events-auto">
            <ThreeCoreCanvas className="w-full h-full" />
          </div>
        </div>

        <p className="text-base md:text-lg text-slate-600 max-w-2xl mx-auto font-medium leading-relaxed">
          AgentX deploys specialized AI teammates for Support, Sales, and Operations. 
          They formulate multi-step plans, execute tools through n8n & MCP, verify outputs, and keep human operators in control.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
          <button
            onClick={() => setActiveTab('create-task')}
            className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-extrabold shadow-lg shadow-indigo-600/25 transition-all hover:scale-105"
          >
            <Play className="w-4 h-4 fill-current" />
            <span>Try Live Demo ("Investigate Complaint")</span>
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-slate-800 border border-slate-200 text-sm font-bold shadow-xs transition-colors"
          >
            <span>Explore Dashboard</span>
          </button>
        </div>
      </div>

      {/* Clean Product Visual Preview */}
      <div className="max-w-5xl mx-auto w-full z-10 my-8">
        <div className="glass-card rounded-2xl p-6 border border-slate-200 shadow-xl relative overflow-hidden">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-6">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <div className="w-3 h-3 rounded-full bg-amber-400"></div>
              <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
              <span className="text-xs font-mono text-slate-500 font-semibold ml-2">agentx-orchestration-engine // live-session</span>
            </div>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
              Deterministic Guardrails Active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-indigo-300 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center mb-3">
                <UserCheck className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 mb-1">Specialized Teammates</h3>
              <p className="text-xs text-slate-600 leading-relaxed">Support, Sales, and Operations agents with role-tailored capabilities and prompt sandboxes.</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-purple-300 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-600 flex items-center justify-center mb-3">
                <Workflow className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 mb-1">Tool Execution & n8n</h3>
              <p className="text-xs text-slate-600 leading-relaxed">Integrates seamlessly with n8n workflows, MCP servers, Salesforce, Shopify, and SendGrid.</p>
            </div>

            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-amber-300 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-600 flex items-center justify-center mb-3">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="text-sm font-bold text-slate-900 mb-1">Human Approval Gate</h3>
              <p className="text-xs text-slate-600 leading-relaxed">High-risk external communications or payments trigger instant human-in-the-loop signoff.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-6xl mx-auto w-full z-10 pt-8 border-t border-slate-200 flex flex-col md:flex-row items-center justify-between text-xs text-slate-500">
        <p>© 2026 AgentX Platforms Inc. Autonomous Workforce Technology.</p>
        <div className="flex items-center gap-6 mt-4 md:mt-0">
          <span className="hover:text-slate-800 cursor-pointer font-medium">Security Sandbox</span>
          <span className="hover:text-slate-800 cursor-pointer font-medium">n8n Integration</span>
          <span className="hover:text-slate-800 cursor-pointer font-medium">MCP Protocol</span>
        </div>
      </div>

      {/* Login Modal Overlay */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-5">
            <div className="text-center space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto border border-indigo-100">
                <Building2 className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-extrabold text-slate-900">Sign In to AgentX</h3>
              <p className="text-xs text-slate-500">Access your business workspace and AI teammates</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Work Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-50 text-slate-800 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
                <input
                  type="password"
                  defaultValue="••••••••••••"
                  className="w-full bg-slate-50 text-slate-800 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                onClick={() => {
                  setShowLoginModal(false);
                  setActiveTab('dashboard');
                }}
                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs transition-colors shadow-md shadow-indigo-600/20"
              >
                Sign In to Workspace
              </button>

              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-slate-200"></div>
                <span className="flex-shrink mx-4 text-[10px] uppercase font-mono text-slate-400 font-bold">Or SSO</span>
                <div className="flex-grow border-t border-slate-200"></div>
              </div>

              <button
                onClick={() => {
                  setShowLoginModal(false);
                  setActiveTab('dashboard');
                }}
                className="w-full py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs border border-slate-200 flex items-center justify-center gap-2 transition-colors"
              >
                <Key className="w-4 h-4 text-indigo-600" />
                <span>Continue with Okta / SAML SSO</span>
              </button>
            </div>

            <button
              onClick={() => setShowLoginModal(false)}
              className="w-full text-center text-xs text-slate-500 hover:text-slate-800 mt-2 font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
