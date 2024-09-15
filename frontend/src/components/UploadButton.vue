<template>
    <button @click="handleUpload" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded">
      Upload Files
    </button>
    <input type="file" ref="fileInput" class="hidden" @change="uploadFiles" multiple>
  </template>
  
  <script setup>
  import { ref } from 'vue';
  
  const fileInput = ref(null);
  
  const handleUpload = () => {
    fileInput.value.click(); // Trigger file input click
  };
  
  const uploadFiles = (event) => {
    const files = event.target.files;
    // Handle the file upload logic here (send to backend or Firebase)
    console.log(files);
  };
  </script>
  
  <style scoped>
  /* Add scoped styles if needed */
  </style>
  