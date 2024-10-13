<template>
  <div class="bg-sky-100 flex justify-center items-center h-screen">
    <!-- Left: Image (visible on large screens) -->
    <div class="w-1/2 h-screen hidden lg:block">
      <img src="https://img.freepik.com/fotos-premium/imagen-fondo_910766-187.jpg?w=826" alt="Placeholder Image" class="object-cover w-full h-full">
    </div>
    <!-- Right: Register Form -->
    <div class="lg:p-36 md:p-52 sm:20 p-8 w-full lg:w-1/2 bg-white dark:bg-gray-800 rounded-md shadow-md">
      <h1 class="text-2xl font-semibold mb-4 dark:text-white">Register</h1>
      <form @submit.prevent="register">
        <!-- Name Input -->
        <div class="mb-4">
          <label for="name" class="block text-gray-600 dark:text-gray-300">Name</label>
          <input
            v-model="name"
            id="name"
            type="text"
            required
            class="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
          />
        </div>
        <!-- Email Input -->
        <div class="mb-4">
          <label for="email" class="block text-gray-600 dark:text-gray-300">Email</label>
          <input
            v-model="email"
            id="email"
            type="email"
            required
            class="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
            autocomplete="off"
          />
        </div>
        <!-- Password Input -->
        <div class="mb-4">
          <label for="password" class="block text-gray-600 dark:text-gray-300">Password</label>
          <input
            v-model="password"
            id="password"
            type="password"
            required
            class="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
            autocomplete="off"
          />
        </div>
        <!-- Confirm Password Input -->
        <div class="mb-4">
          <label for="confirmPassword" class="block text-gray-600 dark:text-gray-300">Confirm Password</label>
          <input
            v-model="confirmPassword"
            id="confirmPassword"
            type="password"
            required
            class="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
            autocomplete="off"
          />
        </div>
        <!-- Error Message -->
        <p v-if="errorMessage" class="text-red-500 mb-4">{{ errorMessage }}</p>
        <!-- Register Button with Spinner -->
        <button type="submit" class="bg-red-500 hover:bg-blue-600 text-white font-semibold rounded-md py-2 px-4 w-full flex items-center justify-center" :disabled="loading">
          <svg v-if="loading" class="animate-spin h-5 w-5 mr-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span v-if="!loading">Register</span>
          <span v-if="loading">Registering...</span>
        </button>
      </form>
      <!-- Login Link -->
      <p class="mt-6 text-green-500 text-center">
        Already have an account? <router-link to="/login" class="hover:underline">Login Here</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { useFaceStore } from '../stores/FaceStore'; // Import Pinia store

const name = ref(null);
const email = ref(null);
const password = ref(null);
const confirmPassword = ref(null);
const errorMessage = ref(null);
const loading = ref(false); // Loading state for the spinner
const router = useRouter();

// Get Pinia store instance
const faceStore = useFaceStore();
const authStore = useAuthStore();

const register = async () => {
  try {
    loading.value = true;
    errorMessage.value = '';
    if (password.value !== confirmPassword.value) {
      errorMessage.value = 'Passwords do not match';
      loading.value = false;
      return;
    }
    await authStore.register(name.value, email.value, password.value);
    await faceStore.loadFaceData();
    loading.value = false;
    router.push('/login');
  } catch (error) {
    loading.value = false;
    errorMessage.value = error.message;
    console.log(error);
  }
};
</script>
