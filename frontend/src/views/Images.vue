<script setup>
import { ref } from 'vue';
import axios from 'axios'; // Import axios for making API calls

// Reactive variables for search query, loading, and suggestions
const searchQuery = ref('');
const showDropdown = ref(false);
const images = ref([]); // To hold the images returned by the backend
const loading = ref(false); // Loading state to show/hide the spinner

// Sample search suggestions
const suggestions = ref(['Mountains', 'Forests', 'Rivers', 'Deserts', 'Oceans', 'Waterfalls', 'Lakes', 'Plains', 'Rainforests', 'Beaches']);

// Filtered suggestions based on search query
const filteredSuggestions = ref([]);

// Filter suggestions when typing in the search bar
const filterSuggestions = () => {
  if (searchQuery.value) {
    filteredSuggestions.value = suggestions.value.filter(suggestion =>
      suggestion.toLowerCase().includes(searchQuery.value.toLowerCase())
    );
  } else {
    filteredSuggestions.value = [];
  }
};

// Fetch images based on search query using POST request
const fetchImages = async (query) => {
  loading.value = true; // Set loading to true when starting the request
  try {
    const response = await axios.post(
      'http://127.0.0.1:5000/images/search_images', 
      { query }, // Send query as JSON payload
      {
        headers: {
          'Content-Type': 'application/json' // Explicitly set the content type
        }
      }
    );
    
    // Assuming 'response.data.images' contains an array of image paths
    images.value = response.data.images.map(imagePath => `http://127.0.0.1:5000/${imagePath}`);
  } catch (error) {
    console.error("Error fetching images:", error);
    images.value = [];
  } finally {
    loading.value = false; // Set loading to false when request completes
  }
};

// Select a suggestion from the dropdown and fetch images
const selectSuggestion = (suggestion) => {
  searchQuery.value = suggestion;
  showDropdown.value = false; // Close dropdown after selection
  fetchImages(suggestion); // Fetch images for the selected suggestion
};

// Hide dropdown after losing focus (with delay to allow click event)
const hideDropdown = () => {
  setTimeout(() => {
    showDropdown.value = false;
  }, 100);
};
</script>

<template>
  <div>
    <!-- Search Bar with Suggestions -->
    <div class="relative mb-4">
      <input
        type="text"
        v-model="searchQuery"
        class="p-2 border rounded-lg w-full"
        placeholder="Search nature images"
        @input="filterSuggestions"
        @focus="showDropdown = true"
        @blur="hideDropdown"
      />

      <!-- Search Suggestions Dropdown -->
      <div v-if="showDropdown && filteredSuggestions.length" class="absolute bg-white border border-gray-300 rounded-lg mt-1 w-full shadow-lg">
        <div
          v-for="(suggestion, index) in filteredSuggestions"
          :key="index"
          class="p-2 hover:bg-gray-100 cursor-pointer"
          @mousedown.prevent="selectSuggestion(suggestion)"
        >
          {{ suggestion }}
        </div>
      </div>
    </div>

    <!-- Loading Spinner -->
    <div v-if="loading" class="flex justify-center items-center">
      <div class="spinner"></div> <!-- Spinner element -->
    </div>

    <!-- Nature Images Grid -->
    <div v-if="images.length && !loading" class="grid grid-cols-4 gap-1">
      <div v-for="(image, index) in images" :key="index">
        <img
          :src="image"
          alt="Nature Image"
          class="rounded-lg"
        />
      </div>
    </div>
    
    <div v-else-if="!loading">
      <p>No images found for "{{ searchQuery }}"</p>
    </div>
  </div>
</template>

<style scoped>
/* Custom styles for the images */
img {
  object-fit: cover;
  width: 300px;
  height: 300px;
}

/* Style for the search input */
input {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* Spinner Styles */
.spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-left-color: #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
