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
        <div class="flex items-center flex-wrap p-1 pl-3 bg-gray-100 dark:bg-gray-700 rounded-lg focus-within:ring-2 focus-within:ring-blue-500">
          <!-- Pills inside the search input -->
          <div class="flex flex-wrap items-center gap-2">
            <div v-for="(word, index) in selectedWords" :key="index" class="flex items-center bg-blue-500 text-white rounded-lg p-1">
              {{ word }}
              <button @click="removeWord(index)" class="ml-1 text-white">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-10.707a1 1 0 00-1.414 0L10 9.586l-2.293-2.293a1 1 0 00-1.414 1.414L8.586 11l-2.293 2.293a1 1 0 101.414 1.414L10 12.414l2.293 2.293a1 1 0 001.414-1.414L11.414 11l2.293-2.293a1 1 0 000-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Search input -->
          <input
            type="text"
            v-model="searchQuery"
            class="flex-1 p-2 bg-transparent outline-none dark:text-white"
            placeholder="Search in Drive"
            @input="filterSuggestions"
            @focus="showDropdown = true" 
            @blur="hideDropdown" 
          />

          <!-- Search button -->
          <button @click="performSearch" class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-800 dark:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 10-14 0 7 7 0 0014 0z" />
            </svg>
          </button>
        </div>

        <!-- Dropdown for Suggested Words and Faces -->
        <div v-if="showDropdown && (filteredSuggestions.length || mockFaces.length)" class="absolute z-10 bg-white dark:bg-gray-800 border border-gray-300 rounded-lg mt-2 shadow-lg p-2">
          <!-- Suggested Words -->
          <div v-if="filteredSuggestions.length">
            <h3 class="text-sm font-semibold dark:text-white">Suggested Words:</h3>
            <div v-for="(suggestion, index) in filteredSuggestions" :key="index" class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer" @mousedown.prevent="addWord(suggestion)">
              {{ suggestion }}
            </div>
          </div>

          <!-- Suggested Faces -->
          <div class="mt-2">
            <h3 class="text-sm font-semibold dark:text-white">Suggested Faces:</h3>
            <div class="flex space-x-2 mt-1">
              <div v-for="(face, index) in mockFaces" :key="index" class="flex-shrink-0 cursor-pointer" @click="selectFace(face)">
                <img :src="face.imgUrl" alt="Face" class="rounded-full w-10 h-10 object-cover" />
              </div>
            </div>
            <button @click="browseAllFaces" class="mt-2 text-blue-500 hover:bg-gray-100 dark:hover:bg-gray-700">
              Browse All Faces
            </button>
          </div>
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

const showDropdown = ref(false); // Dropdown initially hidden
const searchQuery = ref('');
const selectedWords = ref([]);
const suggestions = ref(["Face recognition", "Image classification", "Object detection", "Cloud storage", "Drive files"]);
const filteredSuggestions = ref([]);

// Mock faces data
const mockFaces = [
  { imgUrl: 'https://randomuser.me/api/portraits/men/1.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/women/1.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/men/2.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/women/2.jpg' }
];

// Filter suggestions as the user types
const filterSuggestions = () => {
  showDropdown.value = searchQuery.value !== ''; // Show dropdown while typing
  filteredSuggestions.value = suggestions.value.filter(suggestion =>
    suggestion.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
};

// Add selected word as a pill (up to 5 words)
const addWord = (word) => {
  if (!selectedWords.value.includes(word) && selectedWords.value.length < 5) {
    selectedWords.value.push(word);
  }
  searchQuery.value = ''; // Clear search input
  filterSuggestions(); // Update suggestions
};

// Remove a word from the selected words
const removeWord = (index) => {
  selectedWords.value.splice(index, 1);
};

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

// Perform search action (placeholder function)
const performSearch = () => {
  console.log("Searching for:", selectedWords.value, searchQuery.value);
};

// Hide dropdown after losing focus (with delay)
const hideDropdown = () => {
  setTimeout(() => {
    showDropdown.value = false; // Delay hiding to allow click events to register
  }, 200);
};
</script>

<style scoped>
/* Scoped styles can be added here */
</style>
