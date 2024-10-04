import { defineStore } from 'pinia';
import axios from 'axios';

const API_URL = 'http://localhost:5000/auth';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: {
      id: null,
      name: '',
      email: '',
    },
    authenticated: false,
    access_token: null,
    refresh_token: null,
  }),

  getters: {
    isAuthenticated: (state) => state.authenticated,
    getUser: (state) => state.user,
    getAccessToken: (state) => state.access_token,
  },

  actions: {
    // Set up axios interceptor for JWT
    setupInterceptor() {
      axios.interceptors.request.use(
        (config) => {
          if (this.access_token) {
            config.headers['Authorization'] = `Bearer ${this.access_token}`;
          }
          return config;
        },
        (error) => {
          return Promise.reject(error);
        }
      );

      // Response interceptor for handling token refresh
      axios.interceptors.response.use(
        (response) => response,
        async (error) => {
          const originalRequest = error.config;

          if (error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
              const response = await this.refreshToken();
              if (response) {
                this.access_token = response.data.access_token;
                originalRequest.headers['Authorization'] = `Bearer ${this.access_token}`;
                return axios(originalRequest);
              }
            } catch (refreshError) {
              this.logout();
              return Promise.reject(refreshError);
            }
          }
          return Promise.reject(error);
        }
      );
    },

    // Register new user
    async register(name, email, password) {
      try {
        const response = await axios.post(`${API_URL}/register`, {
          name,
          email,
          password,
        });
        return response.data;
      } catch (error) {
        throw error.response?.data?.error || 'Registration failed';
      }
    },

    // Login user
    async login(email, password) {
      try {
        const response = await axios.post(`${API_URL}/login`, {
          email,
          password,
        });

        const { access_token, refresh_token, user } = response.data;
        
        this.access_token = access_token;
        this.refresh_token = refresh_token;
        this.user = user;
        this.authenticated = true;
        console.log(response.data);
        return response.data;
       
      } catch (error) {
        throw error.response?.data?.error || 'Login failed';
      }
    },

    // Refresh token
    async refreshToken() {
      try {
        const response = await axios.post(`${API_URL}/refresh`, {}, {
          headers: {
            'Authorization': `Bearer ${this.refresh_token}`
          }
        });
        return response;
      } catch (error) {
        this.logout();
        throw error.response?.data?.error || 'Token refresh failed';
      }
    },

    // Get current user
    async fetchUser() {
      try {
        const response = await axios.get(`${API_URL}/me`);
        this.user = response.data;
        return response.data;
      } catch (error) {
        throw error.response?.data?.error || 'Failed to fetch user';
      }
    },

    // Request password reset
    async forgotPassword(email) {
      try {
        const response = await axios.post(`${API_URL}/forgot-password`, { email });
        return response.data;
      } catch (error) {
        throw error.response?.data?.error || 'Password reset request failed';
      }
    },

    // Reset password with token
    async resetPassword(token, new_password) {
      try {
        const response = await axios.post(`${API_URL}/reset-password/${token}`, {
          new_password
        });
        return response.data;
      } catch (error) {
        throw error.response?.data?.error || 'Password reset failed';
      }
    },

    // Resend verification email
    async resendVerification(email) {
      try {
        const response = await axios.post(`${API_URL}/resend-verification`, { email });
        return response.data;
      } catch (error) {
        throw error.response?.data?.error || 'Failed to resend verification';
      }
    },

    // Logout
    async logout() {
      this.resetState();
    },

    // Reset store state
    resetState() {
      this.user = {
        id: null,
        name: '',
        email: '',
      };
      this.authenticated = false;
      this.access_token = null;
      this.refresh_token = null;
    },
  },

  persist: {
    enabled: true,
    strategies: [
      {
        key: 'auth',
        storage: localStorage,
        paths: ['user', 'authenticated', 'access_token', 'refresh_token']
      },
    ],
  },
});

