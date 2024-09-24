<template>
    <div class="mt-4">
      <h3 class="text-lg font-semibold dark:text-white">Search Results</h3>
  
      <!-- Display selected words (pills) -->
      <div class="flex flex-wrap gap-2 mb-2">
        <div v-for="(word, index) in selectedWords" :key="index" class="flex items-center bg-blue-500 text-white rounded-lg p-1">
          {{ word }}
        </div>
      </div>
  
      <!-- Display search query -->
      <div v-if="searchQuery" class="mb-4">
        <p class="text-gray-800 dark:text-white">Search Query: {{ searchQuery }}</p>
      </div>
  
      <!-- Image gallery (mockup with random images for now) -->
      <div class="grid grid-cols-3 gap-4">
        <div v-for="(image, index) in searchResults" :key="index">
          <img :src="image" alt="Search result" class="rounded-lg object-cover w-full h-40" />
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, watchEffect } from 'vue';
  
  const props = defineProps({
    selectedWords: Array,
    searchQuery: String
  });
  
  // Mock search results (for now, we'll use random images)
  const searchResults = ref([]);
  
  watchEffect(() => {
    // Simulate fetching images based on selectedWords and searchQuery
    if (props.selectedWords.length > 0 || props.searchQuery) {
      // Mock image URLs, in a real case, you would fetch based on the search parameters
      searchResults.value = [
        'https://picsum.photos/200/300',
        'https://picsum.photos/201/301',
        'https://picsum.photos/202/302',
        'https://picsum.photos/203/303',
        'https://picsum.photos/204/304',
        'https://picsum.photos/205/305'
      ];
    } else {
      searchResults.value = [];
    }
  });
  </script>
  
  <style scoped>
  /* Add styles for search results (optional) */
  </style>
  