import axios from 'axios';

// Resolve Backend API base URL from Vite environment variables, fallback to local dev server
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

// Create Axios Instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request Interceptor to inject active X-Tenant-ID header
api.interceptors.request.use((config) => {
  const activeTenantId = localStorage.getItem('activeTenantId') || '11111111-1111-1111-1111-111111111111'; // seeded Alpha tenant UUID fallback
  config.headers['X-Tenant-ID'] = activeTenantId;
  return config;
}, (error) => {
  return Promise.reject(error);
});

export const apiService = {
  // Health check status
  getStatus: () => api.get('/status/'),

  // Upload Batch Endpoints
  getBatches: (params) => api.get('/batches/', { params }),
  uploadBatch: (file, sourceType) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('source_type', sourceType);
    return api.post('/batches/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
  },

  // Emission Record Endpoints
  getRecords: (params) => api.get('/records/', { params }),
  getSuspiciousRecords: (params) => api.get('/records/suspicious/', { params }),
  getRecordDetail: (id) => api.get(`/records/${id}/`),
  patchRecord: (id, data) => api.patch(`/records/${id}/`, data),
  approveRecord: (id, comments = '') => api.post(`/records/${id}/approve/`, { comments }),
  rejectRecord: (id, comments = '') => api.post(`/records/${id}/reject/`, { comments }),
  unlockRecord: (id) => api.post(`/records/${id}/unlock/`),

  // Audit Logs
  getAuditLogs: (params) => api.get('/audit-logs/', { params }),
};

export default api;
