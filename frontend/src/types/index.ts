export type NavTab = 
  | 'welcome' 
  | 'dashboard' 
  | 'agents' 
  | 'agent-detail' 
  | 'create-task' 
  | 'task-execution' 
  | 'approvals' 
  | 'support-review' 
  | 'task-history' 
  | 'integrations' 
  | 'analytics' 
  | 'settings';

export type AgentRole = 'support' | 'sales' | 'operations';

export type TaskStatus = 
  | 'CREATED'
  | 'PLANNING'
  | 'EXECUTING'
  | 'WAITING_FOR_APPROVAL'
  | 'VERIFYING'
  | 'COMPLETED'
  | 'ESCALATED'
  | 'FAILED';

export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' | 'EXTERNAL_COMMUNICATION' | 'FINANCIAL_TRANSACTION';

export interface ExecutionStep {
  id: string;
  stepIndex: number;
  label: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'WAITING' | 'FAILED';
  toolUsed?: string;
  timestamp: string;
  actionSummary: string;
  details?: {
    input?: Record<string, any>;
    output?: Record<string, any>;
    rawResponse?: string;
    executionTimeMs?: number;
  };
}

export interface TaskItem {
  id: string;
  title: string;
  description: string;
  agentRole: AgentRole;
  agentName: string;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: string;
  durationMs: number;
  currentStepIndex: number;
  steps: ExecutionStep[];
  approvalRequest?: ApprovalRequest;
  supportReview?: SupportReviewData;
  filesAttached?: { name: string; size: string; type: string }[];
  resultSummary?: string;
  verificationReport?: {
    verified: boolean;
    criteriaChecked: string[];
    riskScore: number;
    notes: string;
  };
}

export interface ApprovalRequest {
  id: string;
  taskId: string;
  taskTitle: string;
  agentRole: AgentRole;
  agentName: string;
  toolName: string;
  riskLevel: RiskLevel;
  whyRequired: string;
  proposedAction: string;
  payloadPreview: Record<string, any>;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  rejectionReason?: string;
  createdAt: string;
}

export interface SupportReviewData {
  customerName: string;
  customerEmail: string;
  ticketId: string;
  orderId: string;
  sentiment: 'Very Negative' | 'Negative' | 'Neutral' | 'Positive';
  intent: string;
  severity: 'High' | 'Medium' | 'Low';
  complaintText: string;
  orderContext: {
    item: string;
    amount: string;
    orderDate: string;
    shippingStatus: string;
    trackingNumber: string;
    lifetimeValue: string;
  };
  aiRecommendation: string;
  aiConfidence: number;
  selectedOption?: string;
  customResponseText?: string;
  executedStatus?: string;
}

export interface AgentInfo {
  role: AgentRole;
  name: string;
  title: string;
  avatar: string;
  description: string;
  status: 'Online' | 'Busy' | 'Idle';
  uptime: string;
  tasksCompleted: number;
  successRate: number;
  avgResponseTime: string;
  capabilities: string[];
  tools: { name: string; category: string; icon: string; status: 'Active' | 'Restricted' }[];
  handledTaskTypes: string[];
}

export interface ToolIntegration {
  id: string;
  name: string;
  category: string;
  description: string;
  status: 'Connected' | 'Configured' | 'Disconnected';
  isN8n?: boolean;
  isMCP?: boolean;
  iconName: string;
  availableTools: string[];
  permissionLevel: 'Full Autonomy' | 'Approval Required' | 'Read Only';
}

export interface AnalyticsMetrics {
  tasksCompleted: number;
  successRate: number;
  avgCompletionTime: string;
  actionsExecuted: number;
  escalatedTasks: number;
  agentUtilization: {
    role: AgentRole;
    name: string;
    activeTasks: number;
    completionRate: number;
    avgTimeSec: number;
  }[];
  tasksByAgent: { role: string; count: number }[];
  tasksOverTime: { date: string; completed: number; escalated: number; failed: number }[];
}
