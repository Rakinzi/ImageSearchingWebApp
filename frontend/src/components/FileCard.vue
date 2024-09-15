<template>
    <div class="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-md">
      <div class="flex items-center space-x-4">
        <img :src="file.icon" alt="file icon" class="w-12 h-12">
        <div class="flex-grow">
          <h3 class="text-gray-800 dark:text-white font-semibold">{{ file.name }}</h3>
          <p class="text-sm text-gray-500 dark:text-gray-300">{{ file.size }}</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  defineProps({
    file: {
      type: Object,
      required: true,
    },
  });
  </script>
  
  <style scoped>
  /* Scoped styles */
  </style>
  