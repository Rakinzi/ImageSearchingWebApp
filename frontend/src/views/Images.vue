<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useFaceStore } from '../stores/FaceStore';
import { BASE_URL, IMAGE_URL } from '../stores/urls';

const faceStore = useFaceStore();
const { isLoading, allImages } = faceStore;

 
const searchQuery = ref('');
const loading = ref(false);
const displayedImages = ref([]);

onMounted(async () => {
  updateDisplayedImages();
});

const updateDisplayedImages = () => {
  console.log(faceStore.faceData);
  displayedImages.value = allImages ? allImages.images.map(imagePath => `${BASE_URL + imagePath}`) : [];
};

const fetchImages = async (query) => {
  loading.value = true;
  try {
    const response = await axios.post(
      `${IMAGE_URL}/search_images`, 
      { query },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    
    displayedImages.value = response.data.images.map(imagePath => `${BASE_URL + imagePath}`);
  } catch (error) {
    console.error("Error fetching images:", error);
    displayedImages.value = [];
  } finally {
    loading.value = false;
  }
};

const handleKeyPress = (event) => {
  if (event.key === 'Enter') {
    if (searchQuery.value.trim() !== '') {
      fetchImages(searchQuery.value);
    } else {
      updateDisplayedImages();
    }
  }
};
</script>

<template>
  <div>
    <div class="relative mb-4">
      <input
        type="text"
        v-model="searchQuery"
        class="p-2 border rounded-lg w-full"
        placeholder="Search images"
        @keyup="handleKeyPress"
      />
    </div>

    <div v-if="isLoading || loading" class="flex items-center justify-center min-h-screen">
      <div class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4 lg:grid-cols-3">
      <div v-for="(image, index) in displayedImages" :key="index">
        <img :src="image" class="h-auto max-w-sm rounded-lg" alt="">
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
