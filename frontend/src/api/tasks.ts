import apiClient from './client';
import type {
  BackendTaskDetailResponse,
  TaskCreateRequest,
  TaskExecuteResponse,
  TaskExecutionDetailResponse,
  TaskInputsResponse,
  TaskPlanRequest,
  TaskPlanResponse,
  TaskResponse,
} from '../types/api';

export const tasksApi = {
  /**
   * Create and immediately run a business task through the orchestrator.
   */
  async createTask(request: TaskCreateRequest): Promise<TaskResponse> {
    return apiClient.post<TaskResponse>('/tasks', request);
  },

  /**
   * Generate an execution plan for a business request without executing it yet.
   */
  async generatePlan(request: TaskPlanRequest): Promise<TaskPlanResponse> {
    return apiClient.post<TaskPlanResponse>('/tasks/plan', request);
  },

  /**
   * Execute an existing task plan.
   */
  async executeTask(taskId: string): Promise<TaskExecuteResponse> {
    return apiClient.post<TaskExecuteResponse>(`/tasks/${taskId}/execute`);
  },

  /**
   * Retrieve task information, status, result, and lifecycle events.
   */
  async getTask(taskId: string): Promise<BackendTaskDetailResponse> {
    return apiClient.get<BackendTaskDetailResponse>(`/tasks/${taskId}`);
  },

  /**
   * Retrieve detailed execution trace, step statuses, verification, and approval data.
   */
  async getTaskExecution(taskId: string): Promise<TaskExecutionDetailResponse> {
    return apiClient.get<TaskExecutionDetailResponse>(`/tasks/${taskId}/execution`);
  },

  /**
   * List recent tasks tracked by the backend.
   */
  async listTasks(limit: number = 50): Promise<BackendTaskDetailResponse[]> {
    return apiClient.get<BackendTaskDetailResponse[]>('/tasks', { limit });
  },

  /**
   * Get all multimodal inputs attached to a task.
   */
  async getTaskInputs(taskId: string): Promise<TaskInputsResponse> {
    return apiClient.get<TaskInputsResponse>(`/tasks/${taskId}/inputs`);
  },
};

export default tasksApi;
