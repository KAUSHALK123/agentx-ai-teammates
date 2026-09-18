import apiClient from './client';
import type {
  InputDetailResponse,
  InputProcessResponse,
  InputUploadResponse,
  TaskInputsResponse,
} from '../types/api';

export const inputsApi = {
  /**
   * Upload a business input file (PDF, CSV, DOCX, Image, Audio, or Text).
   */
  async uploadInput(file: File, taskId?: string): Promise<InputUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (taskId) {
      formData.append('task_id', taskId);
    }

    return apiClient.post<InputUploadResponse>('/inputs/upload', formData);
  },

  /**
   * Retrieve full extraction details, status, and structured data for an input.
   */
  async getInput(inputId: string): Promise<InputDetailResponse> {
    return apiClient.get<InputDetailResponse>(`/inputs/${inputId}`);
  },

  /**
   * Trigger or re-run processing/extraction on an uploaded input.
   */
  async processInput(inputId: string): Promise<InputProcessResponse> {
    return apiClient.post<InputProcessResponse>(`/inputs/${inputId}/process`);
  },

  /**
   * Get all multimodal inputs attached to a task.
   */
  async getTaskInputs(taskId: string): Promise<TaskInputsResponse> {
    return apiClient.get<TaskInputsResponse>(`/tasks/${taskId}/inputs`);
  },
};

export default inputsApi;
