import type { AgentInfo, TaskItem, ToolIntegration, AnalyticsMetrics } from '../types';

export const INITIAL_AGENTS: Record<string, AgentInfo> = {
  support: {
    role: 'support',
    name: 'Support Teammate',
    title: 'Customer Resolution Specialist',
    avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    description: 'Handles customer inquiries, investigates order delays, processes refunds within guardrails, drafts empathetic updates, and manages ticket escalations.',
    status: 'Online',
    uptime: '99.9%',
    tasksCompleted: 1420,
    successRate: 98.4,
    avgResponseTime: '1.4s',
    capabilities: [
      'Customer Identification & Verification',
      'Order & ERP Status Lookup',
      'Automated Refund Processing (< $200)',
      'Empathetic Response Generation',
      'Zendesk / Intercom Sync',
      'Escalation Routing'
    ],
    tools: [
      { name: 'Customer Database API', category: 'CRM', icon: 'Database', status: 'Active' },
      { name: 'Shopify / ERP Lookup', category: 'E-Commerce', icon: 'ShoppingBag', status: 'Active' },
      { name: 'Stripe Refund Gateway', category: 'Payments', icon: 'CreditCard', status: 'Restricted' },
      { name: 'Zendesk Ticket Manager', category: 'Support', icon: 'LifeBuoy', status: 'Active' },
      { name: 'Gmail / Email Dispatcher', category: 'Communication', icon: 'Mail', status: 'Restricted' },
    ],
    handledTaskTypes: ['Order Delay Investigation', 'Refund Request Audit', 'Shipping Loss Claim', 'VIP Account Dispute']
  },
  sales: {
    role: 'sales',
    name: 'Sales Teammate',
    title: 'Commercial & Lead Growth Specialist',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    description: 'Enriches inbound sales leads, drafts hyper-personalized outbound outreach, inspects CRM deals, schedules demo calls, and generates quote proposals.',
    status: 'Online',
    uptime: '99.8%',
    tasksCompleted: 980,
    successRate: 96.8,
    avgResponseTime: '2.1s',
    capabilities: [
      'Lead Enrichment & Qualification',
      'HubSpot / Salesforce Deal Update',
      'Personalized Outbound Email Crafting',
      'Meeting Scheduler Integration',
      'Pricing & Discount Calculator',
      'Competitor Signal Monitoring'
    ],
    tools: [
      { name: 'Salesforce API Connector', category: 'CRM', icon: 'Briefcase', status: 'Active' },
      { name: 'Clearbit Lead Enrichment', category: 'Data', icon: 'Search', status: 'Active' },
      { name: 'SendGrid Email Outreach', category: 'Communication', icon: 'Send', status: 'Restricted' },
      { name: 'Calendly Booking Sync', category: 'Scheduling', icon: 'Calendar', status: 'Active' },
      { name: 'Google Sheets Pipeline Sync', category: 'Database', icon: 'FileSpreadsheet', status: 'Active' },
    ],
    handledTaskTypes: ['Lead Score Enrichment', 'Proposal Quote Generator', 'Outbound Prospect Outreach', 'Contract Renewal Review']
  },
  operations: {
    role: 'operations',
    name: 'Operations Teammate',
    title: 'Logistics & Inventory Orchestrator',
    avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    description: 'Monitors supply chain disruptions, audits stock thresholds across warehouses, updates inventory ERP, triggers automated reorders, and manages vendor queries.',
    status: 'Online',
    uptime: '100%',
    tasksCompleted: 1150,
    successRate: 99.1,
    avgResponseTime: '1.8s',
    capabilities: [
      'Warehouse Stock Auditing',
      'Supplier Invoice Reconciliation',
      'n8n Workflow Execution Trigger',
      'Carrier Tracking Investigation',
      'Automated PO Reorder Generator',
      'Anomaly Alerting'
    ],
    tools: [
      { name: 'n8n Automation Engine', category: 'Workflow', icon: 'Workflow', status: 'Active' },
      { name: 'NetSuite ERP Connector', category: 'Operations', icon: 'Layers', status: 'Active' },
      { name: 'FedEx / DHL Tracking API', category: 'Logistics', icon: 'Truck', status: 'Active' },
      { name: 'MCP Warehouse Server', category: 'Protocol', icon: 'Server', status: 'Active' },
      { name: 'Slack Ops Alerting', category: 'Notifications', icon: 'MessageSquare', status: 'Active' },
    ],
    handledTaskTypes: ['Stock Outage Investigation', 'Purchase Order Verification', 'Carrier Delay Tracking', 'Vendor Invoice Audit']
  }
};

export const INITIAL_TASKS: TaskItem[] = [
  {
    id: 'TASK-9042',
    title: 'Investigate customer complaint: Order #ORD-8821 delayed with missing items',
    description: 'Customer Kaushal (k8849819@gmail.com) reported high dissatisfaction with order #ORD-8821. Package delivered late and 1 item missing.',
    agentRole: 'support',
    agentName: 'Support Teammate',
    status: 'WAITING_FOR_APPROVAL',
    priority: 'HIGH',
    createdAt: '12 minutes ago',
    durationMs: 8400,
    currentStepIndex: 5,
    filesAttached: [{ name: 'customer_email_thread.pdf', size: '1.2 MB', type: 'PDF' }],
    steps: [
      {
        id: 's1',
        stepIndex: 1,
        label: 'Understand request & extract parameters',
        status: 'COMPLETED',
        timestamp: '19:04:12',
        actionSummary: 'Extracted Customer: Kaushal, Order: ORD-8821, Issue: Shipping Delay & Missing Item',
        details: { input: { rawText: 'Investigate customer complaint for Order ORD-8821' }, output: { orderId: 'ORD-8821', sentiment: 'Negative', priority: 'High' } }
      },
      {
        id: 's2',
        stepIndex: 2,
        label: 'Select Support Teammate & load guardrails',
        status: 'COMPLETED',
        timestamp: '19:04:14',
        actionSummary: 'Matched task intent to Support Teammate. Policy limit: $200 max auto-refund.',
        details: { input: { requiredRole: 'support' }, output: { maxRefundGuardrail: 200, policyChecked: true } }
      },
      {
        id: 's3',
        stepIndex: 3,
        label: 'Identify customer profile & LTV',
        status: 'COMPLETED',
        toolUsed: 'customer_crm_api',
        timestamp: '19:04:16',
        actionSummary: 'Found Customer #CUST-4912. Status: Premium VIP. Lifetime Spend: $4,850.',
        details: { input: { email: 'k8849819@gmail.com' }, output: { vipStatus: true, LTV: 4850 } }
      },
      {
        id: 's4',
        stepIndex: 4,
        label: 'Check order & shipment status in ERP',
        status: 'COMPLETED',
        toolUsed: 'shopify_erp_lookup',
        timestamp: '19:04:19',
        actionSummary: 'Order ORD-8821 total $145. Carrier tracking indicates warehouse shortage during transit.',
        details: { input: { orderId: 'ORD-8821' }, output: { status: 'Delivered Partial', items: 2, missingItem: 'Wireless Headphones ($89)' } }
      },
      {
        id: 's5',
        stepIndex: 5,
        label: 'Check transaction & formulate resolution',
        status: 'COMPLETED',
        toolUsed: 'stripe_gateway',
        timestamp: '19:04:22',
        actionSummary: 'Calculated replacement re-shipment + $25 inconvenience voucher. Formulated customer response.',
        details: { input: { orderId: 'ORD-8821', voucher: 25 }, output: { proposedAction: 'Send Email & Issue $25 Voucher' } }
      },
      {
        id: 's6',
        stepIndex: 6,
        label: 'Verify result against business policy',
        status: 'WAITING',
        toolUsed: 'policy_verifier',
        timestamp: '19:04:24',
        actionSummary: 'Requires Human Approval: External email dispatch to VIP Customer + $25 Store Credit.',
        details: { input: { action: 'send_external_email' }, output: { approvalNeeded: true, riskLevel: 'EXTERNAL_COMMUNICATION' } }
      },
      {
        id: 's7',
        stepIndex: 7,
        label: 'Complete task & notify customer',
        status: 'PENDING',
        timestamp: 'Pending approval',
        actionSummary: 'Task awaiting manager sign-off to execute final email response.',
      }
    ],
    approvalRequest: {
      id: 'APP-1029',
      taskId: 'TASK-9042',
      taskTitle: 'Investigate customer complaint: Order #ORD-8821',
      agentRole: 'support',
      agentName: 'Support Teammate',
      toolName: 'send_customer_email',
      riskLevel: 'EXTERNAL_COMMUNICATION',
      whyRequired: 'Action involves issuing store credit and sending an unedited external response to a VIP customer.',
      proposedAction: 'Send apology email, issue $25 store voucher, and initiate expedited reshipment of missing Wireless Headphones.',
      payloadPreview: {
        to: 'k8849819@gmail.com',
        subject: 'Apology regarding Order #ORD-8821 + Free Reshipment Update',
        voucherCode: 'AGX-KAUSHAL25',
        replacementOrder: 'RES-9910',
        message: 'Dear Kaushal, We deeply apologize for the missing item in your recent order...'
      },
      status: 'PENDING',
      createdAt: '10 minutes ago'
    },
    supportReview: {
      customerName: 'Kaushal',
      customerEmail: 'k8849819@gmail.com',
      ticketId: 'TICK-8841',
      orderId: 'ORD-8821',
      sentiment: 'Very Negative',
      intent: 'Refund & Complaint',
      severity: 'High',
      complaintText: 'My order #ORD-8821 arrived 4 days late and the Wireless Headphones were missing from the box! I paid for express shipping. Please resolve this immediately or I am canceling my subscription.',
      orderContext: {
        item: 'Pro Audio Bundle (Headphones + Mic)',
        amount: '$145.00',
        orderDate: 'Sept 14, 2026',
        shippingStatus: 'Partial Delivery (Carrier Delay)',
        trackingNumber: '1Z9999999999999999',
        lifetimeValue: '$4,850 (VIP Gold)'
      },
      aiRecommendation: 'Issue immediate complimentary replacement for missing Headphones ($89 value), credit $25 voucher for shipping delay, and dispatch personalized apology.',
      aiConfidence: 0.96
    }
  },
  {
    id: 'TASK-9038',
    title: 'Enrich lead data & draft outbound proposal for Enterprise prospect CloudCorp',
    description: 'Received contact request from VP of IT at CloudCorp (500-1000 employees). Enrich profile via Clearbit, check CRM for existing deals, and draft custom proposal.',
    agentRole: 'sales',
    agentName: 'Sales Teammate',
    status: 'COMPLETED',
    priority: 'MEDIUM',
    createdAt: '1 hour ago',
    durationMs: 4200,
    currentStepIndex: 5,
    resultSummary: 'Enriched lead CloudCorp (ARR potential $45k/yr), created Salesforce lead #LD-552, and drafted personalized proposal stored in Google Docs.',
    verificationReport: {
      verified: true,
      criteriaChecked: ['Clearbit enrichment complete', 'Salesforce duplicate check passed', 'Proposal pricing verified'],
      riskScore: 0.05,
      notes: 'All parameters verified against standard tier pricing.'
    },
    steps: [
      { id: 's1', stepIndex: 1, label: 'Understand request & parse domain', status: 'COMPLETED', timestamp: '18:15:02', actionSummary: 'Extracted prospect domain: cloudcorp.io, contact: Mark Vance (VP IT)' },
      { id: 's2', stepIndex: 2, label: 'Select Sales Teammate', status: 'COMPLETED', timestamp: '18:15:03', actionSummary: 'Routed to Sales Teammate. Loaded Enterprise Pricing Matrix.' },
      { id: 's3', stepIndex: 3, label: 'Enrich lead profile via Clearbit API', status: 'COMPLETED', toolUsed: 'clearbit_enrichment', timestamp: '18:15:05', actionSummary: 'Retrieved CloudCorp profile: 850 employees, Tech sector, $120M Revenue.' },
      { id: 's4', stepIndex: 4, label: 'Update Salesforce CRM lead record', status: 'COMPLETED', toolUsed: 'salesforce_crm_api', timestamp: '18:15:07', actionSummary: 'Created Lead record #LD-552, assigned score 92/100 to Enterprise Pipeline.' },
      { id: 's5', stepIndex: 5, label: 'Verify result & finalize proposal', status: 'COMPLETED', toolUsed: 'task_verifier', timestamp: '18:15:09', actionSummary: 'Verified lead enrichment accuracy and created draft proposal document.' }
    ]
  },
  {
    id: 'TASK-9035',
    title: 'Audit stock outage & trigger n8n automated PO reorder for Warehouse B',
    description: 'Safety stock alert triggered for SKU-9012 (Microchip Controller). Stock level dropped below 50 units.',
    agentRole: 'operations',
    agentName: 'Operations Teammate',
    status: 'COMPLETED',
    priority: 'CRITICAL',
    createdAt: '3 hours ago',
    durationMs: 6100,
    currentStepIndex: 5,
    resultSummary: 'Verified NetSuite stock count (38 units left), executed n8n webhook workflow to issue Purchase Order PO-7712 to Supplier MicroTech Inc.',
    verificationReport: {
      verified: true,
      criteriaChecked: ['Stock threshold confirmed <50', 'Supplier PO auto-approved under $5,000', 'n8n workflow exit code 200'],
      riskScore: 0.02,
      notes: 'PO value $3,400 within auto-purchase limit.'
    },
    steps: [
      { id: 's1', stepIndex: 1, label: 'Understand request', status: 'COMPLETED', timestamp: '16:30:00', actionSummary: 'Detected stock alert SKU-9012 Warehouse B' },
      { id: 's2', stepIndex: 2, label: 'Select Operations Teammate', status: 'COMPLETED', timestamp: '16:30:01', actionSummary: 'Assigned to Operations Teammate' },
      { id: 's3', stepIndex: 3, label: 'Check NetSuite ERP inventory', status: 'COMPLETED', toolUsed: 'netsuite_erp', timestamp: '16:30:03', actionSummary: 'Confirmed 38 units remaining (Threshold 50)' },
      { id: 's4', stepIndex: 4, label: 'Trigger n8n Purchase Order workflow', status: 'COMPLETED', toolUsed: 'n8n_workflow_engine', timestamp: '16:30:05', actionSummary: 'Triggered n8n flow ID #n8n-po-reorder. Generated PO-7712' },
      { id: 's5', stepIndex: 5, label: 'Verify result', status: 'COMPLETED', toolUsed: 'task_verifier', timestamp: '16:30:06', actionSummary: 'Verified PO dispatch with supplier confirmation code #SUP-991' }
    ]
  }
];

export const INITIAL_INTEGRATIONS: ToolIntegration[] = [
  {
    id: 'int-n8n',
    name: 'n8n Workflow Engine',
    category: 'Automation & Workflows',
    description: 'Orchestrates multi-step business automation workflows, Webhooks, and node pipelines.',
    status: 'Connected',
    isN8n: true,
    iconName: 'Workflow',
    availableTools: ['n8n_trigger_webhook', 'n8n_execute_scenario', 'n8n_get_execution_status'],
    permissionLevel: 'Full Autonomy'
  },
  {
    id: 'int-mcp',
    name: 'MCP (Model Context Protocol) Server',
    category: 'Protocol & Tools',
    description: 'Standardized agent-to-tool protocol server for secure external system inspection.',
    status: 'Connected',
    isMCP: true,
    iconName: 'Server',
    availableTools: ['mcp_query_database', 'mcp_read_file_system', 'mcp_execute_code_sandbox'],
    permissionLevel: 'Approval Required'
  },
  {
    id: 'int-crm',
    name: 'Salesforce & HubSpot CRM',
    category: 'Sales & Customer Data',
    description: 'Customer data lookup, deal pipeline updates, lead score enrichment, and contact sync.',
    status: 'Connected',
    iconName: 'Briefcase',
    availableTools: ['crm_lookup_lead', 'crm_update_deal', 'crm_create_contact'],
    permissionLevel: 'Full Autonomy'
  },
  {
    id: 'int-sheets',
    name: 'Google Sheets & Drive',
    category: 'Document Storage',
    description: 'Spreadsheet lookup, pipeline logging, document creation, and batch data export.',
    status: 'Connected',
    iconName: 'FileSpreadsheet',
    availableTools: ['sheets_append_row', 'sheets_read_range', 'drive_upload_file'],
    permissionLevel: 'Full Autonomy'
  },
  {
    id: 'int-email',
    name: 'SendGrid & Gmail',
    category: 'Communication',
    description: 'Transactional email delivery, customer response dispatch, and outbound sales emails.',
    status: 'Connected',
    iconName: 'Mail',
    availableTools: ['send_customer_email', 'send_internal_notification', 'read_inbox_thread'],
    permissionLevel: 'Approval Required'
  },
  {
    id: 'int-erp',
    name: 'Shopify & NetSuite ERP',
    category: 'E-Commerce & Supply Chain',
    description: 'Order fulfillment status, stock level check, refund processing, and warehouse tracking.',
    status: 'Connected',
    iconName: 'ShoppingBag',
    availableTools: ['erp_get_order', 'erp_check_inventory', 'erp_issue_refund'],
    permissionLevel: 'Approval Required'
  }
];

export const INITIAL_ANALYTICS: AnalyticsMetrics = {
  tasksCompleted: 3550,
  successRate: 98.2,
  avgCompletionTime: '1.7 min',
  actionsExecuted: 18420,
  escalatedTasks: 28,
  agentUtilization: [
    { role: 'support', name: 'Support Teammate', activeTasks: 4, completionRate: 98.4, avgTimeSec: 84 },
    { role: 'sales', name: 'Sales Teammate', activeTasks: 2, completionRate: 96.8, avgTimeSec: 112 },
    { role: 'operations', name: 'Operations Teammate', activeTasks: 5, completionRate: 99.1, avgTimeSec: 95 }
  ],
  tasksByAgent: [
    { role: 'Support', count: 1420 },
    { role: 'Sales', count: 980 },
    { role: 'Operations', count: 1150 }
  ],
  tasksOverTime: [
    { date: 'Mon', completed: 420, escalated: 3, failed: 1 },
    { date: 'Tue', completed: 510, escalated: 4, failed: 2 },
    { date: 'Wed', completed: 630, escalated: 2, failed: 1 },
    { date: 'Thu', completed: 590, escalated: 5, failed: 0 },
    { date: 'Fri', completed: 720, escalated: 6, failed: 2 },
    { date: 'Sat', completed: 340, escalated: 4, failed: 1 },
    { date: 'Sun', completed: 340, escalated: 4, failed: 0 }
  ]
};
