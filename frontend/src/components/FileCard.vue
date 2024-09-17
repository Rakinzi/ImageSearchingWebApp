<template>
  <transition name="fade">
    <div v-if="visible" class="bg-white dark:bg-gray-800 rounded-lg py-2 shadow-md flex flex-col items-center space-y-4">
      <!-- File Image -->
      <img :src="file.url" alt="file icon" class="w-full mb-4">

      <!-- File Name and Size -->
      <div class="text-center">
        <h3 class="text-gray-800 dark:text-white font-semibold">{{ file.name }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-300">{{ file.size }}</p>
      </div>

      <!-- Delete Button -->
      <button @click="deleteFile" class="mt-4 bg-red-500 text-white py-1 px-4 rounded-md">
        Delete
      </button>
    </div>
  </transition>
</template>

<script setup>
import { ref } from 'vue';
import { deleteObject, ref as storageRef } from "firebase/storage";
import { storage } from '../services/firebase'; // import Firebase storage

const props = defineProps({
  file: {
    type: Object,
    required: true,
  },
});

// Track the visibility of the component for animation
const visible = ref(true);

const deleteFile = async () => {
  try {
    // Create a reference to the file in Firebase Storage
    const storageReference = storageRef(storage, `uploads/${props.file.name}`);

    // Delete the file
    await deleteObject(storageReference);
    console.log("File deleted successfully!");

    // Animate and hide the component
    visible.value = false;

    // Optionally, emit an event to refresh the file list
    // emit('fileDeleted', props.file.id);
  } catch (error) {
    console.error("Error deleting file:", error.message);
  }
};
</script>

<style scoped>
/* Make the image larger and center text */


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
