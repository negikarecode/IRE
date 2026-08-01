/**
 * Production REST API Client for Insurance Reasoning Engine (IRE) FastAPI Backend.
 * 
 * BACKEND-FIRST ARCHITECTURE:
 * - Every entity (Hospital, User, Claim, Document, OCR Result, AI Finding, Appeal, Insurance Payer)
 *   is fetched from and stored in the backend database.
 * - The frontend never owns business data.
 * - If backend is unavailable, proper loading and error states are shown.
 */

const API_BASE_URL = '/api/v1';
const DEFAULT_TENANT_ID = 'tenant_apollo_health';

export interface APIError {
  message: string;
  status?: number;
}

class BackendAPIClient {
  private tenantId: string = DEFAULT_TENANT_ID;

  public setTenantId(tenantId: string) {
    this.tenantId = tenantId;
  }

  private getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'X-Tenant-ID': this.tenantId,
      'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'token_dev_authenticated'}`
    };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = { ...this.getHeaders(), ...options.headers };

    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        let errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
        try {
          const errJson = await response.json();
          console.error(`[Backend API Error] Endpoint: ${endpoint}`, errJson);
          
          // Handle structured error responses
          if (errJson.detail) {
            if (typeof errJson.detail === 'string') {
              errorMsg = errJson.detail;
            } else if (typeof errJson.detail === 'object') {
              // Structured error: { success: false, error: "CODE", message: "..." }
              errorMsg = errJson.detail.message || errJson.detail.error || JSON.stringify(errJson.detail);
            }
          } else if (errJson.message) {
            errorMsg = errJson.message;
          } else if (errJson.error) {
            errorMsg = typeof errJson.error === 'string' ? errJson.error : JSON.stringify(errJson.error);
          }
        } catch (parseErr) {
          console.error(`[Backend API Parse Error] Endpoint: ${endpoint}`, parseErr);
        }
        throw new Error(errorMsg);
      }
      return await response.json();
    } catch (err: any) {
      console.error(`[Backend API Request Failed] Endpoint: ${endpoint}`, err);
      throw err;
    }
  }

  // CLAIMS API
  public async getClaims(): Promise<any[]> {
    return this.request<any[]>('/claims');
  }

  public async getClaimById(id: string): Promise<any> {
    return this.request<any>(`/claims/${id}`);
  }

  public async createClaim(claimPayload: any): Promise<any> {
    return this.request<any>('/claims/', {
      method: 'POST',
      body: JSON.stringify(claimPayload)
    });
  }

  // DOCUMENTS API
  public async getDocuments(): Promise<any[]> {
    return this.request<any[]>('/documents');
  }

  public async getDocument(documentId: string): Promise<any> {
    return this.request<any>(`/documents/${documentId}`);
  }

  public async updateDocumentClassification(documentId: string, documentType: string, confidence?: number): Promise<any> {
    return this.request<any>(`/documents/${documentId}/classification`, {
      method: 'PUT',
      body: JSON.stringify({ document_type: documentType, confidence })
    });
  }

  public async getClinicalExtraction(documentId: string): Promise<any> {
    return this.request<any>(`/documents/${documentId}/clinical`);
  }

  public async deleteDocument(documentId: string): Promise<void> {
    return this.request<void>(`/documents/${documentId}`, {
      method: 'DELETE'
    });
  }

  public async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token') || 'token_dev_authenticated'}`
      },
      body: formData
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    return await response.json();
  }

  // PATIENTS API
  public async getPatients(): Promise<any[]> {
    return this.request<any[]>('/patients');
  }

  public async createPatient(patientPayload: any): Promise<any> {
    return this.request<any>('/patients/', {
      method: 'POST',
      body: JSON.stringify(patientPayload)
    });
  }

  // HOSPITALS & SETTINGS API
  public async getHospitals(): Promise<any[]> {
    return this.request<any[]>('/hospitals');
  }

  public async getSettings(): Promise<any[]> {
    return this.request<any[]>('/settings');
  }

  public async updateSetting(key: string, value: string): Promise<any> {
    return this.request<any>('/settings/', {
      method: 'POST',
      body: JSON.stringify({ key, value })
    });
  }

  // HEALTH CHECK
  public async checkHealth(): Promise<boolean> {
    try {
      const res = await this.request<{ status: string }>('/health');
      return res.status === 'HEALTHY' || res.status === 'OPERATIONAL';
    } catch (_) {
      return false;
    }
  }

  // AUTHENTICATION API
  public async login(email: string, password: string): Promise<{ access_token: string; user_id: string; hospital_name: string; roles: string[] }> {
    return this.request<{ access_token: string; user_id: string; hospital_name: string; roles: string[] }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }

  public async signup(email: string, password: string, fullName: string, hospitalName: string): Promise<{ access_token: string; user_id: string; hospital_name: string; roles: string[] }> {
    return this.request<{ access_token: string; user_id: string; hospital_name: string; roles: string[] }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, hospital_name: hospitalName })
    });
  }

  public async logout(): Promise<void> {
    return this.request<void>('/auth/logout', {
      method: 'POST'
    });
  }

  public async getCurrentUser(): Promise<any> {
    return this.request<any>('/auth/me');
  }
}

export const apiClient = new BackendAPIClient();
