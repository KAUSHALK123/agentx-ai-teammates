import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { SearchModal } from './components/layout/SearchModal';
import { ApprovalModal } from './components/layout/ApprovalModal';

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
import { IntegrationsView } from './components/views/IntegrationsView';
import { AnalyticsView } from './components/views/AnalyticsView';
import { SettingsView } from './components/views/SettingsView';

const MainContent: React.FC = () => {
  const { activeTab } = useApp();

  if (activeTab === 'welcome') {
    return <WelcomeView />;
  }

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
          {activeTab === 'dashboard' && <DashboardView />}
          {activeTab === 'agents' && <AgentsView />}
          {activeTab === 'agent-detail' && <AgentDetailView />}
          {activeTab === 'create-task' && <CreateTaskView />}
          {activeTab === 'task-execution' && <TaskExecutionView />}
          {activeTab === 'approvals' && <HumanApprovalView />}
          {activeTab === 'support-review' && <SupportReviewView />}
          {activeTab === 'task-history' && <TaskHistoryView />}
          {activeTab === 'integrations' && <IntegrationsView />}
          {activeTab === 'analytics' && <AnalyticsView />}
          {activeTab === 'settings' && <SettingsView />}
        </main>
      </div>

      <SearchModal />
      <ApprovalModal />
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <MainContent />
    </AppProvider>
  );
}
