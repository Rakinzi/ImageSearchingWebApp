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
        
        <!-- Display error message -->
        <p v-if="errorMessage" class="text-red-500 mb-4">{{ errorMessage }}</p>

        <!-- Login Button with Spinner -->
        <button type="submit" class="w-full bg-blue-500 text-white py-2 rounded-md flex items-center justify-center" :disabled="loading">
          <svg v-if="loading" class="animate-spin h-5 w-5 mr-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span v-if="!loading">Login</span>
          <span v-if="loading">Logging in...</span>
        </button>

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
import { auth } from '../services/firebase'; 
import { signInWithEmailAndPassword } from 'firebase/auth';

const email = ref('');
const password = ref('');
const errorMessage = ref('');
const loading = ref(false); // Loading state for the spinner
const router = useRouter();

// Map Firebase errors to user-friendly messages
const getFriendlyErrorMessage = (errorCode) => {
  switch (errorCode) {
    case 'auth/invalid-email':
      return 'The email address is not valid.';
    case 'auth/user-disabled':
      return 'This user has been disabled.';
    case 'auth/user-not-found':
      return 'No user found with this email.';
    case 'auth/wrong-password':
      return 'Incorrect password.';
    default:
      return 'An error occurred. Please try again.';
  }
};

const login = async () => {
  errorMessage.value = '';
  loading.value = true; // Start loading spinner

  try {
    const userCredential = await signInWithEmailAndPassword(auth, email.value, password.value);
    console.log("User Logged In:", userCredential.user);
    router.push('/');
  } catch (error) {
    errorMessage.value = getFriendlyErrorMessage(error.code);
  } finally {
    loading.value = false; // Stop loading spinner
  }
};
</script>
