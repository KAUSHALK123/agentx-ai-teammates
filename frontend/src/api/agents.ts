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

  /**
   * Chat dynamically with an AI teammate with Cognee Knowledge grounding and live LLM generation.
   */
  async chatWithAgent(message: string, agentId?: string, workspaceId?: string): Promise<{
    agent_id: string;
    agent_name: string;
    reply: string;
    knowledge_used?: Array<{ source: string; content?: string; score?: number }>;
    task_id?: string;
    suggested_actions?: string[];
    created_at?: string;
  }> {
    return apiClient.post('/agents/chat', {
      message,
      agent_id: agentId,
      workspace_id: workspaceId
    });
  },
};

export default agentsApi;
