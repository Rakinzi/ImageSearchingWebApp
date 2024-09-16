<template>
    <div v-if="showOverlay" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 p-6 rounded-md shadow-md w-96">
        <h2 class="text-2xl font-bold mb-4 dark:text-white">Upload File</h2>
        <input type="file" @change="handleFileUpload" class="mb-4 w-full" />
        <button @click="uploadFile" :disabled="!file" class="w-full bg-blue-500 text-white py-2 rounded-md">
          Upload
        </button>
        <button @click="$emit('close')" class="mt-4 w-full text-blue-500">Cancel</button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, defineProps, defineEmits } from 'vue';
  
  const props = defineProps({
    showOverlay: Boolean
  });
  
  const emit = defineEmits(['close']);
  
  const file = ref(null);
  
  const handleFileUpload = (event) => {
    file.value = event.target.files[0];
  };
  
  const uploadFile = async () => {
    if (!file.value) return;
  
    // Implement file upload logic here
  
    // Close the overlay after upload
    emit('close');
  };
  </script>
  
  <style scoped>
  /* Overlay styles */
  </style>
  