<template>
  <div class="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
    <div class="max-w-md w-full bg-white dark:bg-gray-800 p-6 rounded-md shadow-md">
      <h1 class="text-2xl font-bold mb-4 dark:text-white">Login</h1>
      <form @submit.prevent="login">
        <div class="mb-4">
          <label for="email" class="block text-gray-700 dark:text-gray-300">Email</label>
          <input
            v-model="email"
            id="email"
            type="email"
            required
            class="w-full p-2 border border-gray-300 rounded-md"
          />
        </div>
        <div class="mb-4">
          <label for="password" class="block text-gray-700 dark:text-gray-300">Password</label>
          <input
            v-model="password"
            id="password"
            type="password"
            required
            class="w-full p-2 border border-gray-300 rounded-md"
          />
        </div>
        <button type="submit" class="w-full bg-blue-500 text-white py-2 rounded-md">Login</button>
        <p class="mt-4 text-center dark:text-gray-400">
          Don't have an account? <router-link to="/register" class="text-blue-500">Register</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const email = ref('');
const password = ref('');
const router = useRouter();

const login = async () => {
  // Implement login logic here (e.g., API call)
  try {
    // Example API call
    // const response = await fetch('/api/login', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ email: email.value, password: password.value }),
    // });
    // const data = await response.json();
    
    // Simulate successful login
    router.push('/');
  } catch (error) {
    console.error('Login failed:', error);
  }
};
</script>

<style scoped>
/* Add any additional styling you need */
</style>
