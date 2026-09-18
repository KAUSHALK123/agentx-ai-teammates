import apiClient from './client';
import type {
  ApprovalDecisionResponse,
  ApprovalRejectRequest,
  BackendApprovalResponse,
} from '../types/api';

export const approvalsApi = {
  /**
   * List all pending approval requests awaiting human intervention.
   */
  async listPendingApprovals(): Promise<BackendApprovalResponse[]> {
    return apiClient.get<BackendApprovalResponse[]>('/approvals/pending');
  },

  /**
   * List all approval requests with optional status and task filters.
   */
  async listApprovals(status?: string, taskId?: string): Promise<BackendApprovalResponse[]> {
    return apiClient.get<BackendApprovalResponse[]>('/approvals', {
      status,
      task_id: taskId,
    });
  },

  /**
   * Retrieve a specific approval request by ID.
   */
  async getApproval(approvalId: string): Promise<BackendApprovalResponse> {
    return apiClient.get<BackendApprovalResponse>(`/approvals/${approvalId}`);
  },

  /**
   * Approve a high-risk action and resume task execution.
   */
  async approveAction(approvalId: string, resolvedBy: string = 'human_operator'): Promise<ApprovalDecisionResponse> {
    return apiClient.post<ApprovalDecisionResponse>(`/approvals/${approvalId}/approve`, null, {
      params: { resolved_by: resolvedBy },
    });
  },

  /**
   * Reject a high-risk action, preventing execution and stopping the task.
   */
  async rejectAction(
    approvalId: string,
    reason?: string,
    resolvedBy: string = 'human_operator'
  ): Promise<ApprovalDecisionResponse> {
    const payload: ApprovalRejectRequest = { reason: reason || 'Rejected by operator' };
    return apiClient.post<ApprovalDecisionResponse>(`/approvals/${approvalId}/reject`, payload, {
      params: { resolved_by: resolvedBy },
    });
  },

  /**
   * List all approval requests for a specific task.
   */
  async listTaskApprovals(taskId: string): Promise<BackendApprovalResponse[]> {
    return apiClient.get<BackendApprovalResponse[]>(`/approvals/task/${taskId}`);
  },
};

export default approvalsApi;
