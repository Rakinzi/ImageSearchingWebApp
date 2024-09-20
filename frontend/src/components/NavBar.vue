<template>
  <nav class="bg-white dark:bg-gray-800 p-2 shadow-md flex items-center justify-between">
    <!-- Left side (Logo + Menu Button) -->
    <div class="flex items-center space-x-2">
      <button class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
        <svg class="w-6 h-6 text-gray-800 dark:text-white" fill="currentColor" viewBox="0 0 24 24">
          <path d="M4 6h16M4 12h16m-7 6h7"></path>
        </svg>
      </button>
      <span class="text-lg font-semibold dark:text-white">G Storage</span>
    </div>

    <!-- Middle (Search Bar) -->
    <div class="flex-1 mx-4">
      <div class="relative">
        <input
          type="text"
          placeholder="Search in Drive"
          class="w-full p-2 pl-10 rounded-lg bg-gray-100 dark:bg-gray-700 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          @focus="showDropdown = true"  
          @blur="hideDropdown"           
        />
        <svg
          class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500 dark:text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 10-14 0 7 7 0 0014 0z"></path>
        </svg>

        <!-- Dropdown for Suggested Faces -->
        <div v-if="showDropdown" class="absolute z-10 bg-white dark:bg-gray-800 border border-gray-300 rounded-lg mt-2 shadow-lg p-2 flex space-x-2 overflow-x-auto">
          <div v-for="(face, index) in mockFaces" :key="index" class="flex-shrink-0 cursor-pointer" @click="selectFace(face)">
            <img :src="face.imgUrl" alt="Face" class="rounded-full w-10 h-10 object-cover" />
          </div>
          <button @click="browseAllFaces" class="flex-shrink-0 p-2 text-blue-500 hover:bg-gray-100 dark:hover:bg-gray-700">
            Browse All Faces
          </button>
        </div>
      </div>
    </div>

    <!-- Right side (Actions: Upload, Profile) -->
    <div class="flex items-center space-x-4">
      <!-- Upload Button -->
      <button class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
        <svg
          class="w-6 h-6 text-gray-800 dark:text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2m-4-4l-4-4m0 0l-4 4m4-4v12"
          ></path>
        </svg>
      </button>

      <!-- Profile Icon -->
      <button class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
        <svg
          class="w-6 h-6 text-gray-800 dark:text-white"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5.121 17.804A5.998 5.998 0 0112 15c2.208 0 4.208.896 5.879 2.396M12 7a5 5 0 110-10 5 5 0 010 10zm0 8a7 7 0 00-7 7h14a7 7 0 00-7-7z"
          ></path>
        </svg>
      </button>

      <!-- Dark Mode Toggle -->
      <DarkModeToggle />
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue';
import DarkModeToggle from './DarkModeToggle.vue';

// Show dropdown initially set to false
const showDropdown = ref(false);

// Mock suggested faces data
const mockFaces = [
  { imgUrl: 'https://randomuser.me/api/portraits/men/1.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/women/1.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/men/2.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/women/2.jpg' }
];

// Function to handle face selection
const selectFace = (face) => {
  console.log("Selected face:", face);
  // Implement logic for selecting the face
};

// Function to handle "Browse All Faces"
const browseAllFaces = () => {
  console.log("Browse all faces clicked");
  // Implement navigation to browse all faces
};

// Function to hide dropdown
const hideDropdown = () => {
  setTimeout(() => {
    showDropdown.value = false; // Delay hiding to allow click events to register
  }, 200);
};
</script>

<style scoped>
/* Scoped styles can be added here */
</style>
