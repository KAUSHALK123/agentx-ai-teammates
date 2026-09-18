import React, { useState, useEffect } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { SearchModal } from './components/layout/SearchModal';
import { ApprovalModal } from './components/layout/ApprovalModal';
import { GothicGateEntrance } from './components/ui/GothicGateEntrance';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

// Views
import { WelcomeView } from './components/views/WelcomeView';
import { DashboardView } from './components/views/DashboardView';
import { AgentsView } from './components/views/AgentsView';
import { AgentDetailView } from './components/views/AgentDetailView';
import { CreateTaskView } from './components/views/CreateTaskView';
import { TaskExecutionView } from './components/views/TaskExecutionView';
import { HumanApprovalView } from './components/views/HumanApprovalView';
import { SupportReviewView } from './components/views/SupportReviewView';
import { TaskHistoryView } from './components/views/TaskHistoryView';
import { InputsView } from './components/views/InputsView';
import { IntegrationsView } from './components/views/IntegrationsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { SettingsView } from './components/views/SettingsView';

const MainContent: React.FC = () => {
  const { activeTab, setActiveTab } = useApp();
  const [showGothicEntrance, setShowGothicEntrance] = useState<boolean>(false);

  // Check initial route to respect direct deep-linking
  useEffect(() => {
    const hash = window.location.hash.replace(/^#\/?/, '').trim();
    const path = window.location.pathname.replace(/^\//, '').trim();
    const hasDeepLink = Boolean(hash || (path && path !== 'welcome'));

    const hasOpened = sessionStorage.getItem('agentx_gate_opened');
    if (!hasOpened && !hasDeepLink) {
      setShowGothicEntrance(true);
    } else if (hasDeepLink) {
      sessionStorage.setItem('agentx_gate_opened', 'true');
    }
  }, []);

  // Listen for custom replay event from sidebar/welcome view
  useEffect(() => {
    const handleReplay = () => setShowGothicEntrance(true);
    window.addEventListener('replay-gothic-entrance', handleReplay);
    return () => window.removeEventListener('replay-gothic-entrance', handleReplay);
  }, []);

  if (showGothicEntrance) {
    return (
      <GothicGateEntrance 
        onEnterComplete={() => {
          setShowGothicEntrance(false);
          if (activeTab === 'welcome') {
            setActiveTab('dashboard');
          }
        }} 
      />
    );
  }

  if (activeTab === 'welcome') {
    return (
      <ErrorBoundary fallbackTitle="Welcome View Error">
        <WelcomeView />
        {/* Option to view entrance again */}
        <button
          onClick={() => setShowGothicEntrance(true)}
          className="fixed bottom-4 right-4 z-40 px-4 py-2 bg-[#0d0306] hover:bg-black text-red-400 border border-red-900 rounded-xl text-xs font-bold shadow-2xl transition-all flex items-center gap-2 cursor-pointer"
          style={{ fontFamily: "'Cinzel', serif" }}
        >
          <span>🏰 Replay Gate Entrance</span>
        </button>
      </ErrorBoundary>
    );
  }

  const knownTabs = [
    'dashboard', 'agents', 'agent-detail', 'create-task', 
    'task-execution', 'approvals', 'support-review', 'task-history', 
    'inputs', 'integrations', 'analytics', 'settings'
  ];

  return (
    <div className="flex min-h-screen relative overflow-x-hidden text-slate-800">
      {/* Animated Fluid Mesh Background */}
      <div className="fluid-bg">
        <div className="blob"></div>
        <div className="blob blob-2"></div>
      </div>

      <Sidebar />

      <div className="flex-1 ml-72 min-w-0 flex flex-col min-h-screen">
        <Header />
        <main className="flex-1 p-10 space-y-10">
          <ErrorBoundary fallbackTitle="View Display Error">
            {activeTab === 'dashboard' && <DashboardView />}
            {activeTab === 'agents' && <AgentsView />}
            {activeTab === 'agent-detail' && <AgentDetailView />}
            {activeTab === 'create-task' && <CreateTaskView />}
            {activeTab === 'task-execution' && <TaskExecutionView />}
            {activeTab === 'approvals' && <HumanApprovalView />}
            {activeTab === 'support-review' && <SupportReviewView />}
            {activeTab === 'task-history' && <TaskHistoryView />}
            {activeTab === 'inputs' && <InputsView />}
            {activeTab === 'integrations' && <IntegrationsView />}
            {activeTab === 'analytics' && <AnalyticsView />}
            {activeTab === 'settings' && <SettingsView />}

            {/* Safe fallback if route is unrecognized */}
            {!knownTabs.includes(activeTab) && <DashboardView />}
          </ErrorBoundary>
        </main>
      </div>

      <SearchModal />
      <ApprovalModal />
    </div>
  );
};

export default function App() {
  return (
    <ErrorBoundary fallbackTitle="AgentX System Runtime Error">
      <AppProvider>
        <MainContent />
      </AppProvider>
    </ErrorBoundary>
  );
}
