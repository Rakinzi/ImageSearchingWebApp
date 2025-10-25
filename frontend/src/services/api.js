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
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Set auth token
export const setAuthToken = (token) => {
  authToken = token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    localStorage.setItem('authToken', token)
    console.log('✅ Auth token set successfully')
  } else {
    delete api.defaults.headers.common['Authorization']
    localStorage.removeItem('authToken')
    localStorage.removeItem('userData')
    console.log('🔒 Auth token cleared')
  }
}

// Initialize token from localStorage on app load
const initializeAuth = () => {
  const savedToken = localStorage.getItem('authToken')
  if (savedToken) {
    setAuthToken(savedToken)
    console.log('🔑 Auth token loaded from localStorage')
  }
}

// Call initialization
initializeAuth()

// Request interceptor - Add auth token to every request
api.interceptors.request.use(
  (config) => {
    // Ensure token is always attached if available
    const token = localStorage.getItem('authToken')
    if (token && !config.headers['Authorization']) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, {
      hasAuth: !!config.headers['Authorization']
    })

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
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Check if we're already refreshing
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }

      isRefreshing = true

      try {
        // Try to refresh the token
        const refreshResponse = await api.post('/api/v1/auth/refresh')
        const newToken = refreshResponse.data?.data?.access_token || refreshResponse.data?.access_token

        if (newToken) {
          setAuthToken(newToken)
          processQueue(null, newToken)
          originalRequest.headers['Authorization'] = 'Bearer ' + newToken
          return api(originalRequest)
        } else {
          throw new Error('No token received from refresh')
        }
      } catch (refreshError) {
        console.error('🔄 Token refresh failed:', refreshError)
        processQueue(refreshError, null)

        // Clear auth and redirect to login
        setAuthToken(null)

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