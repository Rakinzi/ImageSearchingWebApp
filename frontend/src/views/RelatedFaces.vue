<template>
    
    <div v-if="relatedImages.length" class="grid grid-cols-1 md:grid-cols-2 gap-4 lg:grid-cols-3 ">
        <div  v-for="(image, index) in relatedImages" :key="index">
            <img  :src="'http://127.0.0.1:5000/' + image" class="h-auto max-w-sm rounded-lg"  alt="">
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
      console.log(response.data.related_images);
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

<style scoped>
img {
  object-fit: cover;
  width: 300px;
  height: 300px;
}

</style>
  