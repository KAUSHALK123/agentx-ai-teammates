/**
 * API Contract Types matching AgentX FastAPI backend Pydantic models.
 */

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface BackendAgentResponse {
  agent_id: string;
  name: string;
  role: string;
  description: string;
  responsibilities: string[];
  capabilities: string[];
  available_tools: string[];
}

export interface TaskCreateRequest {
  user_request: string;
  selected_agent?: string | null;
  input_ids?: string[];
}

export interface TaskResponse {
  task_id: string;
  selected_agent?: string | null;
  status: string;
}

export interface TaskPlanRequest {
  user_request: string;
  selected_agent?: string | null;
}

export interface TaskPlanStep {
  step_id: string;
  description: string;
  tool_name: string;
  input_params?: Record<string, any>;
  order?: number;
  required_approval?: boolean;
  depends_on?: string[];
}

export interface TaskPlanResponse {
  task_id: string;
  selected_agent: string;
  task_category: string;
  confidence: number;
  explanation: string;
  is_ambiguous: boolean;
  clarification_prompt?: string | null;
  plan: {
    task_id: string;
    agent: string;
    objective: string;
    steps: TaskPlanStep[];
  };
}

export interface TaskEvent {
  event_type: string;
  description: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface BackendTaskDetailResponse {
  task_id: string;
  user_request: string;
  selected_agent?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  result?: any;
  error?: string | null;
  approval_required: boolean;
  events: TaskEvent[];
  input_ids?: string[];
}

export interface ExecutionRecord {
  step_id: string;
  tool_name: string;
  start_time: string;
  end_time?: string | null;
  status: string;
  input_payload?: Record<string, any>;
  output_result?: Record<string, any>;
  error?: string | null;
  retry_count?: number;
}

export interface VerificationReportData {
  verified: boolean;
  criteria_checked: string[];
  risk_score: number;
  details?: Record<string, any>;
  notes?: string;
}

export interface TaskExecuteResponse {
  task_id: string;
  status: string;
  selected_agent?: string | null;
  approval?: any;
  final_result?: any;
  error?: string | null;
  message: string;
}

export interface TaskExecutionDetailResponse {
  task_id: string;
  task_status: string;
  selected_agent?: string | null;
  current_step?: string | null;
  steps: TaskPlanStep[];
  execution_records: ExecutionRecord[];
  verification_status?: VerificationReportData | null;
  approval?: BackendApprovalResponse | null;
  final_result?: any;
  error?: string | null;
}

export interface BackendApprovalResponse {
  approval_id: string;
  task_id: string;
  step_id?: string | null;
  agent_id: string;
  action: string;
  tool_id: string;
  risk_level: string;
  reason: string;
  proposed_input: Record<string, any>;
  status: string;
  created_at: string;
  resolved_at?: string | null;
  resolved_by?: string | null;
  rejection_reason?: string | null;
}

export interface ApprovalDecisionResponse {
  approval_id: string;
  task_id: string;
  status: string;
  message: string;
  task_status?: string | null;
  final_result?: any;
}

export interface ApprovalRejectRequest {
  reason?: string;
}

export interface SupportAnalyzeRequest {
  message: string;
  customer_id?: string | null;
}

export interface SupportAnalyzeResponse {
  intent: string;
  confidence: number;
  sentiment?: string | null;
  severity: string;
  customer_context?: Record<string, any> | null;
  recommended_action: string;
  recommended_strategy?: string | null;
  response_options: string[];
  draft_response?: string | null;
  approval_required: boolean;
  explanation?: string | null;
}

export interface SupportCaseResponse {
  case_id: string;
  task_id: string;
  customer_id?: string | null;
  order_id?: string | null;
  transaction_id?: string | null;
  intent: string;
  severity: string;
  status: string;
  issue_summary: string;
  resolution?: string | null;
  escalation_reason?: string | null;
  recommended_human_action?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportExecuteActionRequest {
  task_id?: string | null;
  case_id?: string | null;
  action: string;
  custom_response?: string | null;
  customer_id?: string | null;
}

export interface SupportExecuteActionResponse {
  success: boolean;
  action: string;
  message: string;
  case_id?: string | null;
  task_id?: string | null;
  status: string;
}

export interface InputUploadResponse {
  input_id: string;
  type: string;
  filename: string;
  size_bytes: number;
  mime_type?: string | null;
  status: string;
  metadata: Record<string, any>;
  task_id?: string | null;
  created_at: string;
}

export interface InputDetailResponse {
  input_id: string;
  type: string;
  filename: string;
  content_reference: string;
  size_bytes: number;
  mime_type?: string | null;
  extracted_text?: string | null;
  structured_data?: Record<string, any> | null;
  metadata: Record<string, any>;
  status: string;
  error_code?: string | null;
  error_message?: string | null;
  task_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InputProcessResponse {
  input_id: string;
  type: string;
  status: string;
  extracted_text?: string | null;
  structured_data?: Record<string, any> | null;
  error_code?: string | null;
  error_message?: string | null;
  metadata: Record<string, any>;
}

export interface TaskInputsResponse {
  task_id: string;
  total_inputs: number;
  inputs: InputDetailResponse[];
}

export interface ToolMetadataResponse {
  tool_id: string;
  name: string;
  description: string;
  category: string;
  is_write: boolean;
  input_schema: Record<string, any>;
  output_schema?: Record<string, any>;
}

export interface N8nStatusResponse {
  status: string;
  n8n_base_url?: string;
  healthy?: boolean;
  [key: string]: any;
}
