/**
 * Modern API service layer for frontend-backend communication
 */
import axios from 'axios'

// API Configuration
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
}

// Create axios instance
const api = axios.create(API_CONFIG)

// Auth token management
let authToken = null

// Set auth token
export const setAuthToken = (token) => {
  authToken = token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    localStorage.setItem('authToken', token)
  } else {
    delete api.defaults.headers.common['Authorization']
    localStorage.removeItem('authToken')
  }
}

// Initialize token from localStorage
const savedToken = localStorage.getItem('authToken')
if (savedToken) {
  setAuthToken(savedToken)
}

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth token on 401
      setAuthToken(null)
      // Redirect to login if needed
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Export base URL for use in components
export const API_BASE_URL = API_CONFIG.baseURL

// API endpoints
export const apiService = {
  // Authentication
  auth: {
    login: (credentials) => api.post('/api/v1/auth/login', credentials),
    register: (userData) => api.post('/api/v1/auth/register', userData),
    logout: () => api.post('/api/v1/auth/logout'),
    refreshToken: () => api.post('/api/v1/auth/refresh'),
    forgotPassword: (email) => api.post('/api/v1/auth/forgot-password', { email }),
    resetPassword: (token, newPassword) => api.post(`/api/v1/auth/reset-password/${token}`, { new_password: newPassword }),
    getProfile: () => api.get('/api/v1/auth/me')
  },

  // Images (v2 API)
  images: {
    // List images with pagination and filtering
    list: (params = {}) => api.get('/api/v2/images/', { params }),

    // Get single image
    get: (imageId) => api.get(`/api/v2/images/${imageId}`),

    // Upload images
    upload: (formData, onProgress) => api.post('/api/v2/images/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: onProgress
    }),

    // Delete image
    delete: (imageId) => api.delete(`/api/v2/images/${imageId}`),

    // Search images
    search: (searchData) => api.post('/api/v2/images/search', searchData),

    // Get user statistics
    getStats: () => api.get('/api/v2/images/stats'),

    // Reprocess image
    reprocess: (imageId) => api.post(`/api/v2/images/${imageId}/reprocess`)
  },

  // Faces
  faces: {
    list: (params = {}) => api.get('/api/v1/faces/', { params }),
    get: (faceId) => api.get(`/api/v1/faces/${faceId}`),
    delete: (faceId) => api.delete(`/api/v1/faces/${faceId}`),
    search: (faceId) => api.get(`/api/v1/faces/${faceId}/similar`)
  },

  // Health check
  health: () => api.get('/health')
}

// Error handling utilities
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response
    return {
      status,
      message: data.message || data.error || 'An error occurred',
      details: data.details || null
    }
  } else if (error.request) {
    // Network error
    return {
      status: 0,
      message: 'Network error - please check your connection',
      details: null
    }
  } else {
    // Other error
    return {
      status: -1,
      message: error.message || 'An unexpected error occurred',
      details: null
    }
  }
}

// Upload progress helper
export const createUploadProgressHandler = (onProgress) => {
  return (progressEvent) => {
    const progress = Math.round(
      (progressEvent.loaded * 100) / progressEvent.total
    )
    if (onProgress) {
      onProgress(progress)
    }
  }
}

export default api