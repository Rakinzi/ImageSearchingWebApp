<template>
  <div class="w-full max-w-sm bg-white border border-gray-200 rounded-lg shadow dark:bg-gray-800 dark:border-gray-700 py-3">
    <div class="flex flex-col items-center pb-10">
        <img class="w-24 h-24 mb-3 rounded-full shadow-lg" :src="BASE_URL + faceImage"  alt="Face image"/>
        <div class="flex mt-4 md:mt-6">
            <button @click="$emit('click', extractedFaceId)" class="py-2 px-4 ms-2 text-sm font-medium text-gray-900 focus:outline-none bg-white rounded-lg border border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-4 focus:ring-gray-100 dark:focus:ring-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700">View More</button>
        </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { BASE_URL } from '../stores/urls.js';

const props = defineProps({
  faceImage: {
    type: String,
    required: true
  }
});

const extractedFaceId = computed(() => {
  const match = props.faceImage.match(/(\d+)/);
  return match ? parseInt(match[0]) : null;
});
</script>