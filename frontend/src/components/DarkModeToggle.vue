<template>
    <button @click="toggleDarkMode" class="p-2 bg-gray-200 dark:bg-gray-700 rounded">
      <span v-if="isDarkMode" class="text-white">🌙</span>
      <span v-else class="text-black">☀️</span>
    </button>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const isDarkMode = ref(false);
  
  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value;
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };
  </script>
  
  <style scoped>
  /* Optional scoped styling */
  </style>
  