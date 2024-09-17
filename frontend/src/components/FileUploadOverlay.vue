<template>
    <div v-if="showOverlay" class="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-800 p-6 rounded-md shadow-md w-96">
        <h2 class="text-2xl font-bold mb-4 dark:text-white">Upload Image</h2>
        
        <!-- File Input (Only Images) -->
        <input 
          type="file" 
          accept="image/*" 
          @change="handleFileUpload" 
          class="mb-4 w-full" 
        />
    
        <!-- Image Preview -->
        <div v-if="imageData" class="mb-4 text-center">
          <img :src="imageData" alt="Image preview" class="w-full h-auto">
        </div>
    
        <!-- Upload Button -->
        <button 
          @click="uploadFile" 
          :disabled="!file || isUploading" 
          class="w-full bg-blue-500 text-white py-2 rounded-md"
        >
          <span v-if="isUploading">Uploading...</span>
          <span v-else>Upload</span>
        </button>
    
        <!-- Cancel Button -->
        <button @click="$emit('close')" class="mt-4 w-full text-blue-500">Cancel</button>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, defineProps, defineEmits } from 'vue';
  import { ref as storageRef, uploadBytes } from "firebase/storage";
  import { storage } from '../services/firebase';
  import { useRouter } from 'vue-router'; // Import useRouter for navigation
  
  // Props and emits
  const props = defineProps({
    showOverlay: Boolean
  });
  const emit = defineEmits(['close']);
  
  // Refs
  const file = ref(null);
  const imageData = ref(null); // To hold the image preview data
  const isUploading = ref(false); // Loading state
  
  const router = useRouter(); // Get the router instance
  
  // Handle file input
  const handleFileUpload = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type.startsWith('image/')) {
      file.value = selectedFile;
  
      // Create a URL for preview
      const reader = new FileReader();
      reader.onload = (e) => {
        imageData.value = e.target.result; // Set image preview data
      };
      reader.readAsDataURL(selectedFile);
    } else {
      alert('Please upload an image file.');
    }
  };
  
  // Upload file function
  const uploadFile = async () => {
    if (!file.value) return;
  
    isUploading.value = true;
  
    try {
      const storageReference = storageRef(storage, `uploads/${file.value.name}`);
      const snapshot = await uploadBytes(storageReference, file.value);
  
      console.log("Uploaded a file!", snapshot);
  
      // Clear inputs and close the overlay
      file.value = null;
      imageData.value = null;
      emit('close');
  
      // Redirect to the home page
      router.push('/'); // Navigate to the home page
    } catch (error) {
      console.error("File upload failed:", error.message);
    } finally {
      isUploading.value = false;
    }
  };
  </script>
  
  <style scoped>
  /* Add any overlay or custom styles */
  img {
    max-width: 100%;
    height: auto;
  }
  </style>
  