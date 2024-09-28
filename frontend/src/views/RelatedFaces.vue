<template>
    <!-- <div>
      <h1 class="text-2xl font-bold">Related Faces for Face {{ faceId }}</h1>
      <div v-if="relatedImages.length" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-6">
        <img v-for="(image, index) in relatedImages" :key="index" :src="'http://127.0.0.1:5000/' + image" class="w-full h-auto object-cover">
      </div>
      <div v-else>No related faces found</div>
    </div> -->
    

    <div v-if="relatedImages.length" class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div  v-for="(image, index) in relatedImages" :key="index">
            <img v-for="(image, index) in relatedImages" :key="index" :src="'http://127.0.0.1:5000/' + image" class="h-auto max-w-sm rounded-lg"  alt="">
        </div>
    </div>
    <div v-else>No related faces found</div>

  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import axios from 'axios';
  
  const route = useRoute();
  const faceId = route.params.faceId; // Get face ID from the route params
  const relatedImages = ref([]); // To store related images
  
  const loadRelatedImages = async () => {
    try {
      const response = await axios.get(`http://127.0.0.1:5000/faces/related_images/${faceId}`);
      relatedImages.value = response.data.related_images;
    } catch (error) {
      console.error('Error fetching related images:', error);
    }
  };
  
  // Fetch related images when the component mounts
  onMounted(() => {
    loadRelatedImages();
  });
  </script>
  