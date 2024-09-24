<template>
    <div class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-75" v-if="isVisible">
      <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-auto">
        <button class="absolute top-2 right-2 text-gray-500" @click="close">✖️</button>
        <img :src="file.url" alt="Large File Image" class="w-full h-auto mb-4" />
        <h2 class="text-xl font-semibold dark:text-white">{{ file.name }}</h2>
        <div v-if="file.analysis.length" class="mt-2">
          <h3 class="font-medium dark:text-gray-300">Analysis:</h3>
          <ul>
            <li v-for="(concept, index) in file.analysis" :key="index" class="text-sm dark:text-gray-400">
              {{ concept.name }}: {{ concept.value.$numberDouble }}%
            </li>
          </ul>
        </div>
        <div v-if="details" class="mt-4">
          <h3 class="font-medium dark:text-gray-300">Details:</h3>
          <p class="text-sm dark:text-gray-400">{{ details }}</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, defineProps } from 'vue';
  import axios from 'axios';
  
  const props = defineProps({
    file: Object,
    isVisible: Boolean,
  });
  
  const details = ref('');
  
  const close = () => {
    emit('close'); // Emit an event to close the modal
  };
  
  // Fetch additional details from MongoDB when the file prop changes
  watchEffect(async () => {
    if (props.file) {
      try {
        const response = await axios.get(`http://localhost:5000/details/${props.file.name}`);
        details.value = response.data.details; // Assuming response contains details
      } catch (error) {
        console.error('Error fetching file details:', error);
      }
    }
  });
  </script>
  
  <style scoped>
  /* Add styles specific to FileModal here */
  </style>
  