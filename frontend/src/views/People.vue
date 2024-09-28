<template>
  <!-- Loading Animation for Full Page -->
  <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
    <div
      class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin">
    </div>
  </div>

  <!-- Display face cards in a responsive grid layout -->
  <div v-if="faceData" class="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-1 lg:grid-cols-4 gap-6 mt-6">
    <FaceCard
      v-for="(faceImage, index) in faceData.face_images"
      :key="index"
      :faceImage="faceImage"
      :faceId="index"
      @click="goToRelatedImages(index)" 
    />
  </div>
  

  <div v-else>No Faces Detected</div>
  



</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import FaceCard from '../components/FaceCard.vue';

const isLoading = ref(true); // Loading state
const faceData = ref(null); // Store face data from the API
const router = useRouter(); // Vue Router instance

const loadFaceData = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/faces/process');
    faceData.value = response.data; // Store the response in faceData
    isLoading.value = false;
    console.log('Face data:', faceData.value); // Log the data to the console
  } catch (error) {
    console.error('Error fetching face data:', error);
  }
};

// Function to navigate to related images route
const goToRelatedImages = (faceId) => {
  router.push(`/faces/${faceId}`);
};

// Fetch face data when the component mounts
onMounted(() => {
  loadFaceData();
});
</script>
