<template>
  <div>
    <h1 class="text-3xl font-bold dark:text-white">Files</h1>
    <p class="mt-2 dark:text-gray-400">View and manage your files here.</p>

    <!-- Search Input -->
    <div class="relative mt-4">
      <input
        type="text"
        v-model="searchTerm"
        @input="fetchSuggestions"
        placeholder="Search analysis"
        class="p-2 border rounded w-full"
      />
      
      <!-- Pills for Selected Search Terms -->
      <div class="flex flex-wrap mt-2">
        <span 
          v-for="(term, index) in selectedTerms" 
          :key="index" 
          class="bg-blue-500 text-white px-3 py-1 rounded-full mr-2 flex items-center"
        >
          {{ term }}
          <span 
            class="ml-2 cursor-pointer" 
            @click="removeTerm(index)"
          >
            &times;
          </span>
        </span>
      </div>

      <!-- Dropdown for Suggested Tags -->
      <div v-if="suggestions.length" class="absolute bg-white border rounded shadow-lg mt-1 w-full z-10">
        <ul>
          <li 
            v-for="(suggestion, index) in suggestions.slice(0, 5)" 
            :key="index" 
            class="px-4 py-2 hover:bg-gray-200 cursor-pointer"
            @click="selectSuggestion(suggestion)"
          >
            {{ suggestion }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Loading Animation -->
    <div v-if="isLoading" class="flex items-center justify-center mt-4">
      <div class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Display files from MongoDB -->
    <div v-else class="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div
        v-for="file in files"
        :key="file._id"
        class="file-card border p-4 rounded-lg shadow-lg cursor-pointer"
        @click="openModal(file)"
      >
        <img :src="file.url" alt="File" class="mb-2 w-full h-32 object-cover rounded" />
        <p class="text-lg font-medium">{{ file.fileName }}</p>
        <div 
          v-for="item in file.analysis" 
          :key="item.id" 
          class="mt-1 inline-flex items-center justify-center px-3 py-1 text-sm font-medium text-white bg-blue-500 rounded-full mx-1"
        >
          {{ item.name }}
        </div>
      </div>
    </div>

    <!-- File Modal -->
    <FileModal 
      v-if="isModalVisible" 
      :file="selectedFile" 
      :isVisible="isModalVisible" 
      @close="isModalVisible = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import FileModal from '../components/FileModal.vue';

const files = ref([]); // Reactive list to store files
const isLoading = ref(true); // Loading state
const isModalVisible = ref(false); // Modal visibility state
const selectedFile = ref(null); // Selected file for the modal
const searchTerm = ref(''); // Search term
const suggestions = ref([]); // Suggested tags
const selectedTerms = ref([]); // Store selected search terms

// Function to load files from MongoDB
const loadFiles = async (searchQuery = '') => {
  try {
    isLoading.value = true; // Start loading
    const response = searchQuery 
      ? await axios.get(`http://localhost:5000/search?query=${encodeURIComponent(searchQuery)}`) 
      : await axios.get('http://localhost:5000/files');

    files.value = response.data; // Store the files in the reactive variable
  } catch (error) {
    console.error('Error loading files from MongoDB:', error);
  } finally {
    isLoading.value = false; // Stop loading
  }
};

// Function to fetch suggested analysis tags based on the input
const fetchSuggestions = async () => {
  try {
    if (searchTerm.value.length > 0) {
      const response = await axios.get(`http://localhost:5000/suggestions?query=${encodeURIComponent(searchTerm.value)}`);
      suggestions.value = response.data; // Assuming the API returns an array of suggestions
    } else {
      suggestions.value = []; // Clear suggestions if input is empty
    }
  } catch (error) {
    console.error('Error fetching suggestions:', error);
  }
};

// Function to search files based on the analysis
const searchFiles = () => {
  selectedTerms.value.push(searchTerm.value); // Add search term to selected terms
  loadFiles(selectedTerms.value.join(' ')); // Pass the joined selected terms to loadFiles
  searchTerm.value = ''; // Clear the input after adding to selected terms
  suggestions.value = []; // Clear suggestions
};

// Function to select a suggestion and set it as the search term
const selectSuggestion = (suggestion) => {
  searchTerm.value = suggestion; // Set the search term to the selected suggestion
  suggestions.value = []; // Clear suggestions
  searchFiles(); // Load files based on the selected suggestion
};

// Function to remove a search term
const removeTerm = (index) => {
  selectedTerms.value.splice(index, 1); // Remove term from selected terms
  if (selectedTerms.value.length === 0) {
    loadFiles(); // Reload all files if no search terms remain
  } else {
    loadFiles(selectedTerms.value.join(' ')); // Reload files based on remaining terms
  }
};

// Function to open the modal with file details
const openModal = (file) => {
  selectedFile.value = file; // Set the selected file
  isModalVisible.value = true; // Show the modal
};

// Fetch files when component is mounted
onMounted(() => {
  loadFiles(); // Load all files on mount
});
</script>

<style scoped>
/* Loading spinner style */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.file-card {
  transition: transform 0.2s;
}
.file-card:hover {
  transform: scale(1.05);
}
</style>
