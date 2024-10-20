<template>
  <div class="bg-sky-100 flex justify-center items-center h-screen">
    <!-- Left: Image (visible on large screens) -->
    <div class="w-1/2 h-screen hidden lg:block">
      <img src="https://img.freepik.com/fotos-premium/imagen-fondo_910766-187.jpg?w=826" alt="Placeholder Image" class="object-cover w-full h-full">
    </div>
    <!-- Right: Login Form -->
    <div class="lg:p-36 md:p-52 sm:20 p-8 w-full lg:w-1/2 bg-white dark:bg-gray-800 rounded-md shadow-md">
      <h1 class="text-2xl font-semibold mb-4 dark:text-white">Login</h1>
      <form @submit.prevent="login">
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
          <label for="password" class="block text-gray-800 dark:text-gray-300">Password</label>
          <input
            v-model="password"
            id="password"
            type="password"
            required
            class="w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:border-blue-500"
            autocomplete="off"
          />
        </div>
        <!-- Remember Me Checkbox -->
        <div class="mb-4 flex items-center">
          <input type="checkbox" id="remember" name="remember" class="text-red-500">
          <label for="remember" class="text-green-900 ml-2">Remember Me</label>
        </div>
        <!-- Error Message -->
        <p v-if="errorMessage" class="text-red-500 mb-4">{{ errorMessage }}</p>
        <!-- Forgot Password Link -->
        <div class="mb-6 text-blue-500">
          <a href="#" class="hover:underline">Forgot Password?</a>
        </div>
        <!-- Login Button with Spinner -->
        <button type="submit" class="bg-red-500 hover:bg-blue-600 text-white font-semibold rounded-md py-2 px-4 w-full flex items-center justify-center" :disabled="loading">
          <svg v-if="loading" class="animate-spin h-5 w-5 mr-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span v-if="!loading">Login</span>
          <span v-if="loading">Logging in...</span>
        </button>
      </form>
      <!-- Sign up Link -->
      <div class="mt-6 text-green-500 text-center">
        <router-link to="/register" class="hover:underline">Sign up Here</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/authStore';
import { useFaceStore } from '../stores/FaceStore'; // Import Pinia store
import { BASE_URL, IMAGE_URL } from '../stores/urls';

console.log(IMAGE_URL);

const email = ref(null);
const password = ref(null);
const errorMessage = ref(null);
const loading = ref(false); // Loading state for the spinner
const router = useRouter();

// Get Pinia store instance
const faceStore = useFaceStore();
const authStore = useAuthStore();

const login = async () => {
  loading.value = true;
  try {
    errorMessage.value = '';
    await authStore.login(email.value, password.value);
    await faceStore.loadFaceData();
    await faceStore.loadImageData();
    loading.value = false;
    router.push('/');
  } catch (error) {
    loading.value = false;
    errorMessage.value = error;
    console.log(error);
  }
};
</script>
