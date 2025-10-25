<template>
  <div class="flex min-h-screen items-center justify-center p-6">
    <Card class="w-full max-w-md p-6">
      <!-- Loading State -->
      <div v-if="loading" class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <h2 class="text-2xl font-bold mt-6">Verifying your email...</h2>
      </div>

      <!-- Success State -->
      <div v-if="success" class="text-center">
        <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle class="h-6 w-6 text-green-600" />
        </div>
        <h2 class="text-2xl font-bold mb-4">Email verified successfully!</h2>
        <p class="text-muted-foreground mb-6">
          Your email has been verified. You can now login to your account.
        </p>
        <router-link to="/login">
          <Button size="lg" class="w-full">Go to Login</Button>
        </router-link>
      </div>

      <!-- Error State -->
      <div v-if="error" class="text-center">
        <div class="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <XCircle class="h-6 w-6 text-red-600" />
        </div>
        <h2 class="text-2xl font-bold mb-4">Verification Failed</h2>
        <p class="text-muted-foreground mb-6">{{ errorMessage }}</p>
        <div class="space-y-3">
          <router-link to="/login">
            <Button size="lg" class="w-full">Go to Login</Button>
          </router-link>
          <Button
            @click="resendVerification"
            :disabled="resendLoading"
            variant="outline"
            size="lg"
            class="w-full"
          >
            <span v-if="resendLoading" class="flex items-center justify-center">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-primary mr-2"></div>
              Sending...
            </span>
            <span v-else>Resend Verification Email</span>
          </Button>
        </div>
      </div>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { CheckCircle, XCircle } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { useAuthStore } from '../stores/authStore'

const route = useRoute()
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
    alert('New verification email has been sent. Please check your inbox.')
  } catch (err) {
    alert('Failed to resend verification email. Please try again.')
  } finally {
    resendLoading.value = false
  }
}

onMounted(() => {
  verifyEmail()
})
</script>
