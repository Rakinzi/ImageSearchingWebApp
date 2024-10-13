<template>
  <transition name="fade">
    <div v-if="visible" class="bg-white dark:bg-gray-800 rounded-lg py-2 shadow-md flex flex-col items-center space-y-4">
      <!-- File Image -->
      <img :src="fileSrc" alt="file icon" class="w-full mb-4" />
      <!-- Optional Display Filename -->
      <p class="text-center">{{ props.file }}</p>
      <!-- Delete Button (optional) -->
      <!-- <button @click="deleteFile" class="mt-4 bg-red-500 text-white py-1 px-4 rounded-md">
        Delete
      </button> -->
    </div>
  </transition>
</template>

<script setup>
import { ref, defineProps } from 'vue';
const apiUrl = import.meta.env.VITE_API_URL;

const props = defineProps({
  file: {
    type: String, // Change to Object if needed
    required: true,
  },
});

// Construct the image source URL
const fileSrc = apiUrl + '/files/' + props.file;

// Track the visibility of the component for animation
const visible = ref(true);
</script>

<style scoped>
button {
  transition: background-color 0.2s ease;
}

button:hover {
  background-color: #ff4f4f;
}

/* Fade-out transition */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>
