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
const api = axios.create({
  ...API_CONFIG,
  withCredentials: true
})

// Auth token management (using HttpOnly cookies)
let isRefreshing = false
let failedQueue = []

const processQueue = (error) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  failedQueue = []
}

// No longer needed - tokens are managed via HttpOnly cookies
export const setAuthToken = (token) => {
  // This function is kept for backward compatibility but does nothing
  // Tokens are automatically sent via HttpOnly cookies
  if (token) {
    console.log('✅ Auth token set via HttpOnly cookie')
  } else {
    console.log('🔒 Auth token cleared via HttpOnly cookie')
  }
}

// Request interceptor - Cookies are sent automatically
api.interceptors.request.use(
  (config) => {
    // Ensure credentials are included for cookie-based auth
    config.withCredentials = true

    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`)

    return config
  },
  (error) => {
    console.error('❌ Request interceptor error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor - Handle errors and token refresh
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
      status: response.status
    })
    return response
  },
  async (error) => {
    const originalRequest = error.config

    console.error(`❌ API Error: ${error.config?.method?.toUpperCase()} ${error.config?.url}`, {
      status: error.response?.status,
      message: error.response?.data?.message || error.message
    })

    // Handle 401 Unauthorized
    if (error.response?.status === 401) {
      const isRefreshRequest = originalRequest?.url?.includes('/api/v1/auth/refresh')

      if (isRefreshRequest) {
        isRefreshing = false
        setAuthToken(null)
        processQueue(error, null)
        return Promise.reject(error)
      }

      if (originalRequest._retry) {
        return Promise.reject(error)
      }

      originalRequest._retry = true

      // Check if we're already refreshing
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => {
          // Cookie is automatically sent, just retry the request
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      isRefreshing = true

      try {
        // Try to refresh the token (cookie will be set automatically by backend)
        await api.post('/api/v1/auth/refresh')

        // Process queued requests
        processQueue(null)

        // Retry the original request (cookie is now refreshed)
        return api(originalRequest)
      } catch (refreshError) {
        console.error('🔄 Token refresh failed:', refreshError)
        processQueue(refreshError)

        // Redirect to login if not already there
        if (window.location.pathname !== '/login' &&
            window.location.pathname !== '/register' &&
            window.location.pathname !== '/verify-email') {
          console.log('🔒 Redirecting to login...')
          window.location.href = '/login'
        }

        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Handle other errors
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
