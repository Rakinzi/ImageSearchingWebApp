<template>
  <!-- Loading Animation for Full Page -->
  <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
    <div class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin"></div>
  </div>

  <!-- Display face cards in a responsive grid layout -->
  <div v-if="faceData" class="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-1 lg:grid-cols-4 gap-6 mt-6">
    <FaceCard
      v-for="faceImage in faceData.face_images"
      :key="extractIdFromImage(faceImage)"
      :faceImage="faceImage"
      @click="goToRelatedImages(extractIdFromImage(faceImage))" 
    />
  </div>

  <div v-else>No Faces Detected</div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useFaceStore } from '../stores/FaceStore';  // Import Pinia store
import FaceCard from '../components/FaceCard.vue';

const router = useRouter();
const faceStore = useFaceStore(); // Use the Pinia store

const { isLoading, faceData, loadFaceData } = faceStore; // Destructure the necessary store values

const ReloadFaceData = () => {
  loadFaceData();
  console.log("loadFaceData");
};

const extractIdFromImage = (imageFilename) => {
  const match = imageFilename.match(/faces\\(.*?)(?:\.jpg|\.jpeg|\.png)$/);
  return match ? match[1] : null;
};

const goToRelatedImages = (faceId) => {
  console.log(faceId);
  router.push(`/faces/${faceId}`);
};

// Fetch face data using Pinia when the component mounts
onMounted(() => {
  ReloadFaceData();
});
</script>
