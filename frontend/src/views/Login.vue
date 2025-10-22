<template>
  <n-layout style="min-height: 100vh;">
    <n-layout-content style="padding: 0;">
      <div style="display: flex; min-height: 100vh;">
        <!-- Left: Colored Background - 60% -->
        <div style="width: 60%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center;">
          <div style="text-align: center; color: white; padding: 48px;">
            <n-h1 style="color: white; font-size: 3rem; margin-bottom: 16px;">Welcome Back</n-h1>
            <n-text style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.9);">
              Sign in to continue exploring our image search platform
            </n-text>
          </div>
        </div>

        <!-- Right: Login Form - 40% -->
        <div style="width: 40%; display: flex; align-items: center; justify-content: center; padding: 24px; background: white; min-height: 100vh;">
          <n-card style="width: 100%; max-width: 400px; padding: 24px;" :bordered="false" embedded>
            <n-h2 style="text-align: center; margin-bottom: 32px; color: #333;">Sign In</n-h2>

            <n-form
              ref="formRef"
              :model="formData"
              :rules="rules"
              size="large"
            >
              <n-form-item path="email" label="Email">
                <n-input
                  v-model:value="formData.email"
                  placeholder="Enter your email"
                  type="email"
                  :input-props="{ autocomplete: 'email' }"
                >
                  <template #prefix>
                    <n-icon><mail /></n-icon>
                  </template>
                </n-input>
              </n-form-item>

              <n-form-item path="password" label="Password">
                <n-input
                  v-model:value="formData.password"
                  placeholder="Enter your password"
                  type="password"
                  show-password-on="click"
                  :input-props="{ autocomplete: 'current-password' }"
                >
                  <template #prefix>
                    <n-icon><lock-closed /></n-icon>
                  </template>
                </n-input>
              </n-form-item>

              <n-form-item>
                <n-space justify="space-between" style="width: 100%">
                  <n-checkbox v-model:checked="formData.remember">
                    Remember me
                  </n-checkbox>
                  <n-button text @click="$router.push('/forgot-password')">
                    Forgot password?
                  </n-button>
                </n-space>
              </n-form-item>

              <n-form-item>
                <n-button
                  type="primary"
                  block
                  size="large"
                  :loading="loading"
                  @click="handleLogin"
                >
                  Sign In
                </n-button>
              </n-form-item>
            </n-form>

            <n-divider style="margin: 24px 0;" />

            <n-text style="text-align: center; display: block;">
              Don't have an account?
              <router-link to="/register">
                <n-button text type="primary">Sign up</n-button>
              </router-link>
            </n-text>
          </n-card>
        </div>
      </div>
    </n-layout-content>
  </n-layout>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import {
  NCard,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NCheckbox,
  NDivider,
  NSpace,
  NText,
  NIcon,
  useMessage
} from 'naive-ui'
import { Mail, LockClosed } from '@vicons/ionicons5'
import { useAuthStore } from '../stores/authStore'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

// Form data
const formData = reactive({
  email: '',
  password: '',
  remember: false
})

// Form validation rules
const rules = {
  email: [
    { required: true, message: 'Email is required' },
    { type: 'email', message: 'Please enter a valid email' }
  ],
  password: [
    { required: true, message: 'Password is required' },
    { min: 6, message: 'Password must be at least 6 characters' }
  ]
}

// Form ref and loading state
const formRef = ref(null)
const loading = ref(false)

// Login handler
const handleLogin = async () => {
  try {
    // Validate form
    await formRef.value?.validate()

    loading.value = true

    // Use existing auth store login method
    await authStore.login(formData.email, formData.password)

    message.success('Login successful!')
    router.push('/')

  } catch (error) {
    console.error('Login failed:', error)
    message.error(error?.message || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

