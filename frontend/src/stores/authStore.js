import { defineStore } from 'pinia'
import { apiService, handleApiError } from '../services/api.js'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isAuthenticated: false,
    loading: false,
    error: null,
    initialized: false
  }),

  getters: {
    getUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated && state.user !== null
  },

  actions: {
    // Initialize auth state using server-issued HttpOnly cookies
    async initialize() {
      console.log('🔵 [AuthStore] initialize() called', {
        initialized: this.initialized,
        loading: this.loading,
        isAuthenticated: this.isAuthenticated,
        hasUser: !!this.user
      })

      // Prevent duplicate initialization
      if (this.initialized || this.loading) {
        console.log('⚠️ [AuthStore] Already initialized or initializing, skipping...')
        return
      }

      this.loading = true
      console.log('🔄 [AuthStore] Starting initialization...')

      try {
        // Try to refresh the session to validate existing cookies
        console.log('🔄 [AuthStore] Calling refreshSession()...')
        await this.refreshSession()

        // If successful, fetch the user profile
        console.log('🔄 [AuthStore] Calling fetchProfile()...')
        await this.fetchProfile()

        this.isAuthenticated = true
        this.initialized = true
        console.log('✅ [AuthStore] Auth initialized successfully', {
          user: this.user?.email,
          isAuthenticated: this.isAuthenticated
        })
      } catch (error) {
        // If initialization fails, clear state (but cookies will expire naturally)
        console.log('❌ [AuthStore] Initialization failed:', error)
        this.user = null
        this.isAuthenticated = false
        this.error = null
        this.initialized = true // Mark as initialized even on failure to prevent retries
        if (error?.status && error.status !== 401) {
          console.error('❌ [AuthStore] Non-401 error during initialization:', error.message)
        } else {
          console.log('🔒 [AuthStore] No valid session found (401)')
        }
      } finally {
        this.loading = false
        console.log('🏁 [AuthStore] Initialization complete', {
          initialized: this.initialized,
          isAuthenticated: this.isAuthenticated,
          hasUser: !!this.user
        })
      }
    },

    // Refresh session using HttpOnly cookies
    // The backend will automatically set new cookies in the response
    async refreshSession() {
      console.log('🔄 [AuthStore] refreshSession() called')
      try {
        const response = await apiService.auth.refreshToken()
        console.log('✅ [AuthStore] Token refresh successful', response.data)
        // Cookies are automatically refreshed by the backend
        // No need to manually handle tokens
        return true
      } catch (error) {
        console.log('❌ [AuthStore] Token refresh failed:', error)
        const errorInfo = handleApiError(error)
        throw errorInfo
      }
    },

    // Login
    async login(email, password) {
      console.log('🔐 [AuthStore] login() called for:', email)
      this.loading = true
      this.error = null

      try {
        const response = await apiService.auth.login({ email, password })
        const { user } = response.data.data || response.data

        // Store user data (tokens are in HttpOnly cookies)
        this.user = user
        this.isAuthenticated = true
        this.initialized = true // Mark as initialized after successful login

        console.log('✅ [AuthStore] Login successful', {
          user: user.email,
          isAuthenticated: this.isAuthenticated,
          initialized: this.initialized
        })

        return { success: true, user }
      } catch (error) {
        console.log('❌ [AuthStore] Login failed:', error)
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
      console.log('🔓 [AuthStore] logout() called')
      try {
        // Call backend logout if authenticated
        // Backend will clear the HttpOnly cookies
        if (this.isAuthenticated) {
          console.log('🔄 [AuthStore] Calling backend logout...')
          await apiService.auth.logout()
          console.log('✅ [AuthStore] Backend logout successful')
        }
      } catch (error) {
        console.warn('⚠️ [AuthStore] Logout API call failed:', error)
      } finally {
        // Clear local state regardless of API success
        // Cookies are cleared by the backend's unset_jwt_cookies()
        this.user = null
        this.isAuthenticated = false
        this.error = null
        this.initialized = false // Reset to allow re-initialization after logout
        console.log('✅ [AuthStore] Local state cleared')
      }
    },

    // Fetch user profile
    async fetchProfile() {
      console.log('👤 [AuthStore] fetchProfile() called')
      try {
        const response = await apiService.auth.getProfile()
        const user = response.data.data || response.data

        this.user = user
        this.isAuthenticated = true

        console.log('✅ [AuthStore] Profile fetched:', {
          email: user.email,
          name: user.name,
          isVerified: user.is_verified
        })

        return user
      } catch (error) {
        console.log('❌ [AuthStore] Profile fetch failed:', error)
        const errorInfo = handleApiError(error)
        throw errorInfo
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
    },

    // Set token (deprecated - tokens are now managed via HttpOnly cookies)
    setToken(_token) {
      console.warn('setToken is deprecated - tokens are managed via HttpOnly cookies')
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
