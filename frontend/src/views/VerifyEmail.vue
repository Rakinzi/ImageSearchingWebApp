<!-- src/views/VerifyEmail.vue -->
<template>
    <div class="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div class="w-full max-w-md space-y-8">
        <!-- Loading State -->
        <div v-if="loading" class="text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <h2 class="mt-4 text-xl font-semibold text-gray-900">
            Verifying your email...
          </h2>
        </div>
  
        <!-- Success State -->
        <div v-if="success" class="text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100">
            <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 class="mt-4 text-xl font-semibold text-gray-900">
            Email verified successfully!
          </h2>
          <p class="mt-2 text-gray-600">
            Your email has been verified. You can now login to your account.
          </p>
          <div class="mt-6">
            <router-link 
              to="/login" 
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Go to Login
            </router-link>
          </div>
        </div>
  
        <!-- Error State -->
        <div v-if="error" class="text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 class="mt-4 text-xl font-semibold text-gray-900">
            Verification Failed
          </h2>
          <p class="mt-2 text-sm text-gray-600">
            {{ errorMessage }}
          </p>
          <div class="mt-6 space-y-4">
            <router-link 
              to="/login" 
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Go to Login
            </router-link>
            <div>
              <button
                @click="resendVerification"
                :disabled="resendLoading"
                class="mt-2 inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {{ resendLoading ? 'Sending...' : 'Resend Verification Email' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useAuthStore } from '../stores/authStore'
  
  const route = useRoute()
  const router = useRouter()
  const authStore = useAuthStore()
  
  const loading = ref(true)
  const success = ref(false)
  const error = ref(false)
  const errorMessage = ref('')
  const resendLoading = ref(false)
  
  const verifyEmail = async () => {
    const token = route.query.token
    
    if (!token) {
      error.value = true
      errorMessage.value = 'Invalid verification link. No token provided.'
      loading.value = false
      return
    }
  
    try {
      // Get the token from URL query parameters
      const response = await fetch(`http://localhost:5000/api/auth/verify-email/${token}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
  
      const data = await response.json()
  
      if (response.ok) {
        success.value = true
        error.value = false
      } else {
        error.value = true
        errorMessage.value = data.error || 'Verification failed. Please try again.'
      }
    } catch (err) {
      error.value = true
      errorMessage.value = 'An error occurred during verification. Please try again.'
    } finally {
      loading.value = false
    }
  }
  
  const resendVerification = async () => {
    resendLoading.value = true
    try {
      await authStore.resendVerification()
      errorMessage.value = 'New verification email has been sent. Please check your inbox.'
    } catch (err) {
      errorMessage.value = 'Failed to resend verification email. Please try again.'
    } finally {
      resendLoading.value = false
    }
  }
  
  onMounted(() => {
    verifyEmail()
  })
  </script>