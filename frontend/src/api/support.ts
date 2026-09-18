import apiClient from './client';
import type {
  SupportAnalyzeRequest,
  SupportAnalyzeResponse,
  SupportCaseResponse,
  SupportExecuteActionRequest,
  SupportExecuteActionResponse,
} from '../types/api';

export const supportApi = {
  /**
   * Analyze customer message, complaint, or review for intent, sentiment, and recommended response.
   */
  async analyze(request: SupportAnalyzeRequest): Promise<SupportAnalyzeResponse> {
    return apiClient.post<SupportAnalyzeResponse>('/support/analyze', request);
  },

  /**
   * Execute human-selected resolution or response option.
   */
  async executeAction(request: SupportExecuteActionRequest): Promise<SupportExecuteActionResponse> {
    return apiClient.post<SupportExecuteActionResponse>('/support/execute-action', request);
  },

  /**
   * List all support cases tracked in the workspace.
   */
  async listCases(): Promise<SupportCaseResponse[]> {
    return apiClient.get<SupportCaseResponse[]>('/support/cases');
  },

  /**
   * Get details for a specific support case.
   */
  async getCase(caseId: string): Promise<SupportCaseResponse> {
    return apiClient.get<SupportCaseResponse>(`/support/cases/${caseId}`);
  },
};

export default supportApi;
