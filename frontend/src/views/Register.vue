<template>
  <div class="flex items-center justify-center h-screen bg-gray-100 dark:bg-gray-900">
    <div class="max-w-md w-full bg-white dark:bg-gray-800 p-6 rounded-md shadow-md">
      <h1 class="text-2xl font-bold mb-4 dark:text-white">Register</h1>
      <form @submit.prevent="register">
        <div class="mb-4">
          <label for="email" class="block text-gray-700 dark:text-gray-300">Name</label>
          <input v-model="name" id="name" type="text" required class="w-full p-2 border border-gray-300 rounded-md" />
        </div>
        <div class="mb-4">
          <label for="email" class="block text-gray-700 dark:text-gray-300">Email</label>
          <input v-model="email" id="email" type="email" required
            class="w-full p-2 border border-gray-300 rounded-md" />
        </div>
        <div class="mb-4">
          <label for="password" class="block text-gray-700 dark:text-gray-300">Password</label>
          <input v-model="password" id="password" type="password" required
            class="w-full p-2 border border-gray-300 rounded-md" />
        </div>
        <div class="mb-4">
          <label for="confirmPassword" class="block text-gray-700 dark:text-gray-300">Confirm Password</label>
          <input v-model="confirmPassword" id="confirmPassword" type="password" required
            class="w-full p-2 border border-gray-300 rounded-md" />
        </div>

        <!-- Display error message -->
        <p v-if="errorMessage" class="text-red-500 mb-4">{{ errorMessage }}</p>

        <!-- Register Button with Spinner -->
        <button type="submit" class="w-full bg-blue-500 text-white py-2 rounded-md flex items-center justify-center"
          :disabled="loading">
          <svg v-if="loading" class="animate-spin h-5 w-5 mr-3 text-white" xmlns="http://www.w3.org/2000/svg"
            fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span v-if="!loading">Register</span>
          <span v-if="loading">Registering...</span>
        </button>

        <p class="mt-4 text-center dark:text-gray-400">
          Already have an account? <router-link to="/login" class="text-blue-500">Login</router-link>
        </p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { useFaceStore } from '../stores/faceStore'; // Import Pinia store

const name = ref(null);
const email = ref(null);
const password = ref(null);
const confirmPassword = ref(null);
const errorMessage = ref(null);
const loading = ref(false); // Loading state for the spinner
const router = useRouter();

// Get Pinia store instance
const faceStore = useFaceStore();
const authStore = useAuthStore();''
 const register = async () => {
      try {
        errorMessage.value = '';
        await authStore.register(name.value, email.value, password.value)
        router.push('/login');
        // Handle success
      } catch (error) {
        errorMessage.value = error;
        console.log(error)
      }
    }

</script>



