import apiClient from './client';
import type { N8nStatusResponse, ToolMetadataResponse } from '../types/api';

export const toolsApi = {
  /**
   * List all registered tools in the tool registry.
   */
  async listTools(category?: string): Promise<ToolMetadataResponse[]> {
    return apiClient.get<ToolMetadataResponse[]>('/tools', { category });
  },

  /**
   * Retrieve schema and metadata for a specific tool.
   */
  async getTool(toolId: string): Promise<ToolMetadataResponse> {
    return apiClient.get<ToolMetadataResponse>(`/tools/${toolId}`);
  },

  /**
   * Check connectivity to n8n automation engine and active workflows.
   */
  async getN8nStatus(): Promise<N8nStatusResponse> {
    return apiClient.get<N8nStatusResponse>('/integrations/n8n/status');
  },
};

export default toolsApi;
