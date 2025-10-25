<template>
  <div class="flex min-h-screen">
    <!-- Left: Colored Background - 60% -->
    <div class="w-3/5 bg-gradient-to-br from-indigo-500 via-purple-500 to-purple-700 flex items-center justify-center">
      <div class="text-center text-white p-12">
        <h1 class="text-5xl font-bold mb-4">Welcome Back</h1>
        <p class="text-xl text-white/90">
          Sign in to continue exploring our image search platform
        </p>
      </div>
    </div>

    <!-- Right: Login Form - 40% -->
    <div class="w-2/5 flex items-center justify-center p-6 bg-background min-h-screen">
      <Card class="w-full max-w-md p-6">
        <h2 class="text-3xl font-bold text-center mb-8">Sign In</h2>

        <form @submit.prevent="handleLogin" class="space-y-4">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                id="email"
                v-model="formData.email"
                type="email"
                placeholder="Enter your email"
                class="pl-10"
                autocomplete="email"
                required
              />
            </div>
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <div class="relative">
              <Lock class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                id="password"
                v-model="formData.password"
                type="password"
                placeholder="Enter your password"
                class="pl-10"
                autocomplete="current-password"
                required
              />
            </div>
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <Checkbox id="remember" v-model:checked="formData.remember" />
              <Label for="remember" class="text-sm font-normal cursor-pointer">
                Remember me
              </Label>
            </div>
            <Button variant="link" type="button" @click="$router.push('/forgot-password')" class="p-0">
              Forgot password?
            </Button>
          </div>

          <Button
            type="submit"
            class="w-full"
            size="lg"
            :disabled="loading"
          >
            <span v-if="loading" class="flex items-center">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Signing in...
            </span>
            <span v-else>Sign In</span>
          </Button>
        </form>

        <Separator class="my-6" />

        <p class="text-center text-sm text-muted-foreground">
          Don't have an account?
          <router-link to="/register">
            <Button variant="link" class="p-0 h-auto font-semibold">Sign up</Button>
          </router-link>
        </p>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { Mail, Lock } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useAuthStore } from '../stores/authStore'

const router = useRouter()
const authStore = useAuthStore()

// Form data
const formData = reactive({
  email: '',
  password: '',
  remember: false
})

// Form ref and loading state
const loading = ref(false)

// Login handler
const handleLogin = async () => {
  try {
    loading.value = true

    // Use existing auth store login method
    await authStore.login(formData.email, formData.password)

    // Success - redirect to dashboard
    router.push('/')

  } catch (error) {
    console.error('Login failed:', error)
    alert(error?.message || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>
