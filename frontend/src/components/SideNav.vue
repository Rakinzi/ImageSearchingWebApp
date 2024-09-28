<template>
    <aside class="w-64 bg-white dark:bg-gray-800 h-full shadow-md">
      <div class="p-4">
        <button  @click="openUploadOverlay"  class="p-2 w-full bg-blue-500 text-white rounded-md flex items-center justify-center space-x-2">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
          </svg>
          <span>New</span>
        </button>
      </div>
      
      <nav class="mt-4">
        <ul class="space-y-2">
          <li>
            <router-link to="/" class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7h18M3 12h18m-7 5h7"></path>
              </svg>
              <span>My Drive</span>
            </router-link>
          </li>
          
          <li>
            <router-link to="/images" class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"></path>
              </svg>
              <span>Images</span>
            </router-link>
          </li>
        
          <li>
            <router-link to="/people" class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h14M12 5l7 7-7 7"></path>
              </svg>
              <span>People</span>
            </router-link>
          </li>
          <!-- <li>
            <router-link to="/trash" class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
              <span>Trash</span>
            </router-link>
          </li> -->
        </ul>
      </nav>
    </aside>
  </template>
  
  <script setup>
 
    import { defineEmits } from 'vue';

  const emit = defineEmits(['openUploadOverlay']);

  const openUploadOverlay = () => {
    emit('openUploadOverlay');
  };
  </script>
  
  <style scoped>
  /* Custom styles for SideNav if necessary */
  </style>
  