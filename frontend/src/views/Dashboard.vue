<template>
  <div class="p-4 dark:bg-gray-900 min-h-screen">
    <h1 class="text-3xl font-bold dark:text-white">My Files</h1>

    <!-- Loading Animation -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Display files from Firebase -->
    <div v-else class="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <FileCard v-for="file in files" :key="file.name" :file="file" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { storage } from '../services/firebase'; // Import your Firebase storage
import { listAll, ref as storageRef, getDownloadURL } from 'firebase/storage';
import FileCard from '../components/FileCard.vue';
import UploadButton from '../components/UploadButton.vue';

const files = ref([]); // Create a reactive list to store file information
const isLoading = ref(true); // Create a loading state

// Function to load files from Firebase Storage
const loadFiles = async () => {
  const folderRef = storageRef(storage, 'uploads'); // Specify the folder path in Firebase Storage

  try {
    const result = await listAll(folderRef); // List all files in the folder
    const filePromises = result.items.map(async (fileRef) => {
      const url = await getDownloadURL(fileRef); // Get the file URL
      return {
        name: fileRef.name,
        url: url,
        icon: 'https://via.placeholder.com/50x50.png?text=FILE' // Placeholder icon, update accordingly
      };
    });

    // Resolve all file promises
    files.value = await Promise.all(filePromises);
  } catch (error) {
    console.error('Error loading files:', error);
  } finally {
    isLoading.value = false; // Set loading state to false after loading is complete
  }
};

// Load files when the component is mounted
onMounted(() => {
  loadFiles();
});
</script>

<style scoped>
/* Loading spinner style */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.w-16 {
  width: 4rem;
}
.h-16 {
  height: 4rem;
}
.border-4 {
  border-width: 4px;
}
.border-t-4 {
  border-top-width: 4px;
}
.border-gray-500 {
  border-color: #6b7280;
}
.border-opacity-50 {
  border-opacity: 0.5;
}
.border-t-transparent {
  border-top-color: transparent;
}
.rounded-full {
  border-radius: 9999px;
}
.animate-spin {
  animation: spin 1s linear infinite;
}
</style>

