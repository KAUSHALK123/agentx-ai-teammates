import React, { createContext, useContext, useState, useEffect } from 'react';
import type { NavTab, AgentRole, TaskItem, AgentInfo, ApprovalRequest, ToolIntegration, AnalyticsMetrics, TaskPriority } from '../types';
import { INITIAL_AGENTS, INITIAL_TASKS, INITIAL_INTEGRATIONS, INITIAL_ANALYTICS } from '../mock/data';

interface AppContextType {
  activeTab: NavTab;
  setActiveTab: (tab: NavTab) => void;
  selectedAgentRole: AgentRole;
  setSelectedAgentRole: (role: AgentRole) => void;
  selectedTaskId: string;
  setSelectedTaskId: (id: string) => void;
  tasks: TaskItem[];
  agents: Record<string, AgentInfo>;
  integrations: ToolIntegration[];
  analytics: AnalyticsMetrics;
  activeApprovalModal: ApprovalRequest | null;
  setActiveApprovalModal: (request: ApprovalRequest | null) => void;
  isSearchOpen: boolean;
  setIsSearchOpen: (open: boolean) => void;
  workspace: string;
  setWorkspace: (ws: string) => void;
  
  // Actions
  createNewTask: (params: {
    title: string;
    description: string;
    agentRole: AgentRole | 'auto';
    priority: TaskPriority;
    files?: { name: string; size: string; type: string }[];
  }) => TaskItem;
  
  approveTaskAction: (approvalId: string) => void;
  rejectTaskAction: (approvalId: string, reason?: string) => void;
  executeSupportResponse: (taskId: string, responseType: string, customText?: string) => void;
  startLiveSimulation: (taskId: string) => void;
  isBackendConnected: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<NavTab>('welcome');
  const [selectedAgentRole, setSelectedAgentRole] = useState<AgentRole>('support');
  const [selectedTaskId, setSelectedTaskId] = useState<string>('TASK-9042');
  const [tasks, setTasks] = useState<TaskItem[]>(INITIAL_TASKS);
  const [agents] = useState<Record<string, AgentInfo>>(INITIAL_AGENTS);
  const [integrations] = useState<ToolIntegration[]>(INITIAL_INTEGRATIONS);
  const [analytics] = useState<AnalyticsMetrics>(INITIAL_ANALYTICS);
  const [activeApprovalModal, setActiveApprovalModal] = useState<ApprovalRequest | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [workspace, setWorkspace] = useState<string>('Acme Corp - Global Operations');
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  // Check backend health on mount
  useEffect(() => {
    fetch('/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'ok' || data.status === 'healthy' || data.status === 'operational') {
          setIsBackendConnected(true);
        }
      })
      .catch(() => {
        setIsBackendConnected(false);
      });
  }, []);

  const createNewTask = (params: {
    title: string;
    description: string;
    agentRole: AgentRole | 'auto';
    priority: TaskPriority;
    files?: { name: string; size: string; type: string }[];
  }) => {
    let resolvedRole: AgentRole = 'support';
    if (params.agentRole === 'auto') {
      const descLower = (params.title + ' ' + params.description).toLowerCase();
      if (descLower.includes('lead') || descLower.includes('proposal') || descLower.includes('sale') || descLower.includes('client')) {
        resolvedRole = 'sales';
      } else if (descLower.includes('stock') || descLower.includes('inventory') || descLower.includes('warehouse') || descLower.includes('po') || descLower.includes('n8n')) {
        resolvedRole = 'operations';
      } else {
        resolvedRole = 'support';
      }
    } else {
      resolvedRole = params.agentRole;
    }

    const agentName = agents[resolvedRole]?.name || 'AgentX AI Teammate';
    const newTaskId = `TASK-${Math.floor(1000 + Math.random() * 9000)}`;

    const isCustomerComplaint = params.title.toLowerCase().includes('complaint') || params.description.toLowerCase().includes('complaint');

    const newTask: TaskItem = {
      id: newTaskId,
      title: params.title || 'Investigate customer request',
      description: params.description,
      agentRole: resolvedRole,
      agentName: agentName,
      status: 'PLANNING',
      priority: params.priority,
      createdAt: 'Just now',
      durationMs: 1200,
      currentStepIndex: 1,
      filesAttached: params.files || [],
      steps: [
        {
          id: 'step-1',
          stepIndex: 1,
          label: 'Understand request & parse intent',
          status: 'IN_PROGRESS',
          timestamp: new Date().toLocaleTimeString(),
          actionSummary: `Parsing "${params.title.slice(0, 40)}..."`,
          details: { input: { description: params.description }, output: { intentParsed: true } }
        },
        {
          id: 'step-2',
          stepIndex: 2,
          label: `Select ${agentName} & verify permissions`,
          status: 'PENDING',
          timestamp: 'Upcoming',
          actionSummary: `Routing task to ${agentName} sandbox.`
        },
        {
          id: 'step-3',
          stepIndex: 3,
          label: resolvedRole === 'support' ? 'Identify customer profile & LTV' : resolvedRole === 'sales' ? 'Enrich lead data' : 'Audit stock & ERP parameters',
          status: 'PENDING',
          toolUsed: resolvedRole === 'support' ? 'customer_crm_api' : resolvedRole === 'sales' ? 'clearbit_enrichment' : 'netsuite_erp',
          timestamp: 'Upcoming',
          actionSummary: 'Querying workspace system data.'
        },
        {
          id: 'step-4',
          stepIndex: 4,
          label: resolvedRole === 'support' ? 'Check order transaction status' : resolvedRole === 'sales' ? 'Update CRM deal record' : 'Trigger n8n automation workflow',
          status: 'PENDING',
          toolUsed: resolvedRole === 'support' ? 'stripe_gateway' : resolvedRole === 'sales' ? 'salesforce_crm_api' : 'n8n_workflow_engine',
          timestamp: 'Upcoming',
          actionSummary: 'Interacting with downstream integrations.'
        },
        {
          id: 'step-5',
          stepIndex: 5,
          label: 'Verify result against safety criteria',
          status: 'PENDING',
          toolUsed: 'task_verifier',
          timestamp: 'Upcoming',
          actionSummary: 'Evaluating result accuracy and guardrail compliance.'
        },
        {
          id: 'step-6',
          stepIndex: 6,
          label: 'Complete task & notify workspace',
          status: 'PENDING',
          timestamp: 'Upcoming',
          actionSummary: 'Finalizing task outcome.'
        }
      ],
      supportReview: isCustomerComplaint ? {
        customerName: 'Sarah Jenkins',
        customerEmail: 'sarah.j@acme.com',
        ticketId: 'TICK-9921',
        orderId: 'ORD-8821',
        sentiment: 'Negative',
        intent: 'Complaint & Refund Inquiry',
        severity: 'High',
        complaintText: params.description,
        orderContext: {
          item: 'Pro Wireless Headphones',
          amount: '$89.00',
          orderDate: 'Sept 16, 2026',
          shippingStatus: 'In Transit - Delayed by Carrier',
          trackingNumber: '1Z999888777666',
          lifetimeValue: '$3,200 (Gold VIP)'
        },
        aiRecommendation: 'Dispatch immediate apology email with tracking update and issue $25 store credit voucher.',
        aiConfidence: 0.95
      } : undefined
    };

    setTasks(prev => [newTask, ...prev]);
    setSelectedTaskId(newTaskId);
    setActiveTab('task-execution');

    startLiveSimulation(newTaskId);

    return newTask;
  };

  const startLiveSimulation = (taskId: string) => {
    let stepCount = 1;
    const interval = setInterval(() => {
      stepCount++;
      setTasks(prevTasks => {
        return prevTasks.map(t => {
          if (t.id !== taskId) return t;

          const updatedSteps = t.steps.map((st, idx) => {
            if (idx + 1 < stepCount) {
              return { ...st, status: 'COMPLETED' as const };
            } else if (idx + 1 === stepCount) {
              return { ...st, status: 'IN_PROGRESS' as const, timestamp: new Date().toLocaleTimeString() };
            }
            return st;
          });

          let nextStatus = t.status;
          let duration = t.durationMs + 1000;
          let approval = t.approvalRequest;

          if (stepCount >= 5 && t.agentRole === 'support' && t.title.toLowerCase().includes('complaint') && !t.approvalRequest) {
            nextStatus = 'WAITING_FOR_APPROVAL';
            approval = {
              id: `APP-${Math.floor(1000 + Math.random() * 9000)}`,
              taskId: t.id,
              taskTitle: t.title,
              agentRole: t.agentRole,
              agentName: t.agentName,
              toolName: 'send_customer_email',
              riskLevel: 'EXTERNAL_COMMUNICATION',
              whyRequired: 'Sending external email & store credit voucher to VIP customer requires human approval.',
              proposedAction: 'Dispatch apology email + issue $25 store voucher AGX-RES25.',
              payloadPreview: {
                to: 'sarah.j@acme.com',
                subject: 'Update on Order #ORD-8821 + $25 Voucher',
                voucherCode: 'AGX-RES25',
                reshipmentTracking: '1Z999888777666'
              },
              status: 'PENDING',
              createdAt: 'Just now'
            };
            clearInterval(interval);
          } else if (stepCount > t.steps.length) {
            nextStatus = 'COMPLETED';
            clearInterval(interval);
          } else {
            nextStatus = 'EXECUTING';
          }

          return {
            ...t,
            status: nextStatus,
            currentStepIndex: Math.min(stepCount, t.steps.length),
            durationMs: duration,
            steps: updatedSteps,
            approvalRequest: approval,
            resultSummary: nextStatus === 'COMPLETED' ? `Task successfully executed by ${t.agentName}. All verification checks passed.` : t.resultSummary
          };
        });
      });
    }, 1800);
  };

  const approveTaskAction = (approvalId: string) => {
    setTasks(prev => prev.map(t => {
      if (t.approvalRequest?.id === approvalId) {
        const updatedSteps = t.steps.map(s => ({ ...s, status: 'COMPLETED' as const }));
        return {
          ...t,
          status: 'COMPLETED',
          steps: updatedSteps,
          currentStepIndex: t.steps.length,
          approvalRequest: {
            ...t.approvalRequest,
            status: 'APPROVED'
          },
          resultSummary: `Approved by Human Operator. Task completed by ${t.agentName}. Email & Voucher sent successfully.`,
          verificationReport: {
            verified: true,
            criteriaChecked: ['Human approval granted', 'Email payload validated', 'Voucher limit verified'],
            riskScore: 0.0,
            notes: 'Human operator signed off on action.'
          }
        };
      }
      return t;
    }));
    setActiveApprovalModal(null);
  };

  const rejectTaskAction = (approvalId: string, reason?: string) => {
    setTasks(prev => prev.map(t => {
      if (t.approvalRequest?.id === approvalId) {
        return {
          ...t,
          status: 'ESCALATED',
          approvalRequest: {
            ...t.approvalRequest,
            status: 'REJECTED',
            rejectionReason: reason || 'Action rejected by operator.'
          },
          resultSummary: `Task Escalated: Action rejected by Human Operator (${reason || 'No reason provided'}).`
        };
      }
      return t;
    }));
    setActiveApprovalModal(null);
  };

  const executeSupportResponse = (taskId: string, responseType: string, customText?: string) => {
    setTasks(prev => prev.map(t => {
      if (t.id === taskId && t.supportReview) {
        return {
          ...t,
          status: 'COMPLETED',
          supportReview: {
            ...t.supportReview,
            selectedOption: responseType,
            customResponseText: customText,
            executedStatus: `Response Executed: "${responseType}" via AgentX Support Teammate.`
          },
          resultSummary: `Support Review Resolved: Executed ${responseType} with customer.`
        };
      }
      return t;
    }));
  };

  return (
    <AppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        selectedAgentRole,
        setSelectedAgentRole,
        selectedTaskId,
        setSelectedTaskId,
        tasks,
        agents,
        integrations,
        analytics,
        activeApprovalModal,
        setActiveApprovalModal,
        isSearchOpen,
        setIsSearchOpen,
        workspace,
        setWorkspace,
        createNewTask,
        approveTaskAction,
        rejectTaskAction,
        executeSupportResponse,
        startLiveSimulation,
        isBackendConnected
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
