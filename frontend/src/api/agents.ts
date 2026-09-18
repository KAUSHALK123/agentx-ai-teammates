import apiClient from './client';
import type { BackendAgentResponse } from '../types/api';

export const agentsApi = {
  /**
   * Retrieve all registered AI teammates (Support, Sales, Operations).
   */
  async listAgents(): Promise<BackendAgentResponse[]> {
    return apiClient.get<BackendAgentResponse[]>('/agents');
  },

  /**
   * Retrieve details and capabilities for a specific agent.
   */
  async getAgent(agentId: string): Promise<BackendAgentResponse> {
    return apiClient.get<BackendAgentResponse>(`/agents/${agentId}`);
  },
};

export default agentsApi;
