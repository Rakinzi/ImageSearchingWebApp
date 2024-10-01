<script setup>
import { ref } from 'vue';
import axios from 'axios'; // Import axios for making API calls
import { useFaceStore } from '../stores/faceStore';  // Import Pinia store

const faceStore = useFaceStore(); // Use the Pinia store

const { isLoading, faceData, loadFaceData } = faceStore; // Destructure the necessary store values

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
      </div>
      <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
        <div class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin"></div>
      </div>

    <div v-if="!isLoading"  class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div  v-for="(image, index) in faceData.all_images" :key="index">
            <img  :src="'http://127.0.0.1:5000/' + image" class="h-auto max-w-sm rounded-lg"  alt="">
        </div>
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
