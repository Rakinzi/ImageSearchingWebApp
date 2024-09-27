<template>
    <div @click="loadRelatedImages" class="rounded-lg shadow-lg p-4 bg-white dark:bg-gray-800 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-all">
      <div class="flex items-center justify-center">
        <img
          :src="'http://127.0.0.1:5000/' + faceImage"
          alt="Detected Face"
          class="w-32 h-32 rounded-full object-cover border-4 border-gray-300 dark:border-gray-600"
        />
      </div>
      <div class="mt-4 text-center">
        <p class="text-gray-700 dark:text-gray-300">Detected Face</p>
      </div>
    </div>
  </template>
  
  <script setup>
  import axios from 'axios';
  import { ref } from 'vue';
  
  const props = defineProps({
    faceImage: {
      type: String,
      required: true,
    },
    faceId: {
      type: Number,
      required: true,
    }
  });
  
  // Define the emit event to send data to the parent
  const emit = defineEmits(['relatedImages']);
  
  const loadRelatedImages = async () => {
    try {
      const response = await axios.get(`http://127.0.0.1:5000/faces/related_images/${props.faceId}`);
      
      // Emit the data back to the parent
      emit('relatedImages', response.data);
      
      console.log('Related images:', response.data);  // You can process and display this data as needed
    } catch (error) {
      console.error('Error fetching related images:', error);
    }
  };
  </script>
  