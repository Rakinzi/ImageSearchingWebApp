<template>
  <div class="flex min-h-screen">
    <!-- Left: Colored Background - 60% -->
    <div class="w-3/5 bg-gradient-to-br from-indigo-500 via-purple-500 to-purple-700 flex items-center justify-center">
      <div class="text-center text-white p-12">
        <h1 class="text-5xl font-bold mb-4">Welcome</h1>
        <p class="text-xl text-white/90">
          Create your account to start exploring our image search platform
        </p>
      </div>
    </div>

    <!-- Right: Register Form - 40% -->
    <div class="w-2/5 flex items-center justify-center p-6 bg-background min-h-screen">
      <Card class="w-full max-w-md p-6">
        <h2 class="text-3xl font-bold text-center mb-8">Register</h2>

        <form @submit.prevent="register" class="space-y-4">
          <div class="space-y-2">
            <Label for="name">Name</Label>
            <Input
              id="name"
              v-model="formModel.name"
              placeholder="Enter your name"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="formModel.email"
              type="email"
              placeholder="Enter your email"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="formModel.password"
              type="password"
              placeholder="Enter your password (min 8 characters)"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              v-model="formModel.confirmPassword"
              type="password"
              placeholder="Confirm your password"
              required
            />
          </div>

          <Alert v-if="errorMessage" variant="destructive">
            <AlertDescription>{{ errorMessage }}</AlertDescription>
          </Alert>

          <Button
            type="submit"
            class="w-full"
            size="lg"
            :disabled="loading"
          >
            <span v-if="loading" class="flex items-center">
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Registering...
            </span>
            <span v-else>Register</span>
          </Button>
        </form>

        <Separator class="my-6" />

        <p class="text-center text-sm text-muted-foreground">
          Already have an account?
          <router-link to="/login">
            <Button variant="link" class="p-0 h-auto font-semibold">Login Here</Button>
          </router-link>
        </p>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuthStore } from '../stores/authStore';

const router = useRouter();
const authStore = useAuthStore();

const errorMessage = ref('');
const loading = ref(false);

const formModel = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: ''
});

const register = async () => {
  try {
    loading.value = true;
    errorMessage.value = '';

    // Validate name
    if (formModel.name.length < 2 || formModel.name.length > 100) {
      errorMessage.value = 'Name must be between 2 and 100 characters';
      loading.value = false;
      return;
    }

    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formModel.email)) {
      errorMessage.value = 'Please enter a valid email';
      loading.value = false;
      return;
    }

    // Validate password
    if (formModel.password.length < 8 || formModel.password.length > 128) {
      errorMessage.value = 'Password must be between 8 and 128 characters';
      loading.value = false;
      return;
    }

    // Check password match
    if (formModel.password !== formModel.confirmPassword) {
      errorMessage.value = 'Passwords do not match';
      loading.value = false;
      return;
    }

    await authStore.register({
      name: formModel.name,
      email: formModel.email,
      password: formModel.password
    });

    loading.value = false;

    // Show success and redirect to login
    alert('Registration successful! Please log in to continue.');
    router.push('/login');
  } catch (error) {
    loading.value = false;
    errorMessage.value = error.message || 'Registration failed';
    console.error('Registration error:', error);
  }
};
</script>
