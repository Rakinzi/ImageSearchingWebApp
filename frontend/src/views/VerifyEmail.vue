<!-- src/views/VerifyEmail.vue -->
<template>
  <n-layout style="min-height: 100vh;">
    <n-layout-content style="padding: 0;">
      <div style="display: flex; min-height: 100vh; align-items: center; justify-content: center; padding: 24px;">
        <n-card style="width: 100%; max-width: 400px; padding: 24px;" :bordered="false" embedded>
          <!-- Loading State -->
          <div v-if="loading" style="text-align: center;">
            <n-spin size="large" />
            <n-h2 style="margin-top: 24px; text-align: center;">
              Verifying your email...
            </n-h2>
          </div>

          <!-- Success State -->
          <div v-if="success" style="text-align: center;">
            <n-icon size="48" color="#18a058" style="margin-bottom: 16px;">
              <CheckmarkCircleOutline />
            </n-icon>
            <n-h2 style="text-align: center; margin-bottom: 16px;">
              Email verified successfully!
            </n-h2>
            <n-text style="color: #666;">
              Your email has been verified. You can now login to your account.
            </n-text>
            <div style="margin-top: 24px;">
              <router-link to="/login">
                <n-button type="primary" size="large">
                  Go to Login
                </n-button>
              </router-link>
            </div>
          </div>

          <!-- Error State -->
          <div v-if="error" style="text-align: center;">
            <n-icon size="48" color="#d03050" style="margin-bottom: 16px;">
              <CloseCircleOutline />
            </n-icon>
            <n-h2 style="text-align: center; margin-bottom: 16px;">
              Verification Failed
            </n-h2>
            <n-text style="color: #666; display: block; margin-bottom: 24px;">
              {{ errorMessage }}
            </n-text>
            <n-space vertical>
              <router-link to="/login">
                <n-button type="primary" size="large">
                  Go to Login
                </n-button>
              </router-link>
              <n-button
                @click="resendVerification"
                :loading="resendLoading"
                secondary
              >
                Resend Verification Email
              </n-button>
            </n-space>
          </div>
        </n-card>
      </div>
    </n-layout-content>
  </n-layout>
</template>
  
<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { CheckmarkCircleOutline, CloseCircleOutline } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/authStore'
  
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const message = useMessage()

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
    const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8080'}/api/v1/auth/verify-email/${token}`, {
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
    message.success('New verification email has been sent. Please check your inbox.')
  } catch (err) {
    message.error('Failed to resend verification email. Please try again.')
  } finally {
    resendLoading.value = false
  }
}
  
onMounted(() => {
  verifyEmail()
})
</script>