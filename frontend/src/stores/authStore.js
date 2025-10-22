import { defineStore } from 'pinia'
import { apiService, setAuthToken, handleApiError } from '../services/api.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null
  }),

  getters: {
    getUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null
  },

  actions: {
    // Initialize auth state from localStorage
    async initialize() {
      const token = localStorage.getItem('authToken')
      const userData = localStorage.getItem('userData')

      if (token && userData) {
        try {
          setAuthToken(token)
          this.user = JSON.parse(userData)
          this.isAuthenticated = true

          // Verify token is still valid
          await this.fetchProfile()
        } catch (error) {
          console.warn('Stored auth data invalid, clearing...')
          this.logout()
        }
      }
    },

    // Login
    async login(email, password) {
      this.loading = true
      this.error = null

      try {
        const response = await apiService.auth.login({ email, password })
        const { access_token, user } = response.data.data || response.data

        // Store auth data
        setAuthToken(access_token)
        localStorage.setItem('userData', JSON.stringify(user))

        this.user = user
        this.isAuthenticated = true

        return { success: true, user }
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Register
    async register(userData) {
      this.loading = true
      this.error = null

      try {
        const response = await apiService.auth.register(userData)
        return { success: true, data: response.data }
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Logout
    async logout() {
      try {
        // Call backend logout if authenticated
        if (this.isAuthenticated) {
          await apiService.auth.logout()
        }
      } catch (error) {
        console.warn('Logout API call failed:', error)
      } finally {
        // Clear local state regardless of API success
        this.user = null
        this.isAuthenticated = false
        this.error = null
        setAuthToken(null)
        localStorage.removeItem('userData')
      }
    },

    // Fetch user profile
    async fetchProfile() {
      try {
        const response = await apiService.auth.getProfile()
        const user = response.data.data || response.data

        this.user = user
        localStorage.setItem('userData', JSON.stringify(user))

        return user
      } catch (error) {
        const errorInfo = handleApiError(error)
        throw new Error(errorInfo.message)
      }
    },

    // Forgot password
    async forgotPassword(email) {
      this.loading = true
      this.error = null

      try {
        const response = await apiService.auth.forgotPassword(email)
        return { success: true, data: response.data }
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Reset password
    async resetPassword(token, newPassword) {
      this.loading = true
      this.error = null

      try {
        const response = await apiService.auth.resetPassword(token, newPassword)
        return { success: true, data: response.data }
      } catch (error) {
        const errorInfo = handleApiError(error)
        this.error = errorInfo.message
        throw new Error(errorInfo.message)
      } finally {
        this.loading = false
      }
    },

    // Set user data
    setUser(user) {
      this.user = user
      this.isAuthenticated = true
      localStorage.setItem('userData', JSON.stringify(user))
    },

    // Set token
    setToken(token) {
      setAuthToken(token)
      this.isAuthenticated = true
    },

    // Clear error
    clearError() {
      this.error = null
    }
  },

  persist: {
    enabled: false // We handle persistence manually for better control
  }
})