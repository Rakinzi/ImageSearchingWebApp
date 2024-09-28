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
import { ref, onMounted } from 'vue';
import DarkModeToggle from './DarkModeToggle.vue';
import { useRouter } from 'vue-router';
import { useFaceStore } from '../stores/faceStore';  // Import Pinia store


const showDropdown = ref(false); // Dropdown initially hidden
const searchQuery = ref('');
const selectedWords = ref([]);
const suggestions = ref(["Face recognition", "Image classification", "Object detection", "Cloud storage", "Drive files"]);
const filteredSuggestions = ref([]);


const faceStore = useFaceStore(); // Use the Pinia store



// Mock faces data
const mockFaces = [
  { imgUrl: 'https://randomuser.me/api/portraits/men/1.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/women/1.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/men/2.jpg' },
  { imgUrl: 'https://randomuser.me/api/portraits/women/2.jpg' }
];


const router = useRouter();


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
const selectFace = (faceId) => {
  router.push(`/faces/${faceId}`)
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

