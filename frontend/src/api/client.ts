/**
 * Centralized API client for communicating with the AgentX FastAPI backend.
 * Uses VITE_API_BASE_URL if configured, falling back to relative paths for Vite proxy.
 */

export class ApiClientError extends Error {
  public status: number;
  public data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.data = data;
  }
}

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined | null>): string {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${this.baseUrl}${cleanEndpoint}`, window.location.origin);
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null) {
          url.searchParams.append(key, String(val));
        }
      });
    }
    return this.baseUrl ? url.toString() : `${url.pathname}${url.search}`;
  }

  public async request<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { params, headers: customHeaders, body, ...rest } = options;
    const url = this.buildUrl(endpoint, params);

    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((customHeaders as Record<string, string>) || {}),
    };

    // If body is not FormData, default to application/json
    let formattedBody: BodyInit | undefined = undefined;
    if (body instanceof FormData) {
      formattedBody = body;
    } else if (body !== undefined && body !== null) {
      if (typeof body === 'object') {
        headers['Content-Type'] = 'application/json';
        formattedBody = JSON.stringify(body);
      } else {
        formattedBody = String(body);
      }
    }

    try {
      const response = await fetch(url, {
        ...rest,
        headers,
        body: formattedBody,
      });

      // Parse JSON or text response
      const contentType = response.headers.get('content-type') || '';
      let data: any = null;
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        const errorMsg = data?.detail || data?.message || `Request failed with status ${response.status}`;
        throw new ApiClientError(errorMsg, response.status, data);
      }

      return data as T;
    } catch (err: any) {
      if (err instanceof ApiClientError) {
        throw err;
      }
      throw new ApiClientError(err?.message || 'Network connection to AgentX backend failed', 0, err);
    }
  }

  public get<T = any>(endpoint: string, params?: Record<string, any>, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET', params });
  }

  public post<T = any>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'POST', body });
  }

  public put<T = any>(endpoint: string, body?: any, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'PUT', body });
  }

  public delete<T = any>(endpoint: string, options?: RequestOptions): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();
export default apiClient;
