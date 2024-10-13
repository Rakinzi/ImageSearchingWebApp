<template>
  <aside class="w-64 bg-white dark:bg-gray-800 h-full shadow-md overflow-y-auto" id="style-3">
    <!-- Logo Section -->
    <!-- <div class="p-4 flex justify-center">
      <a href="http://www.creative-tim.com" aria-label="sidebar mini logo" class="simple-text logo-mini">
        <div class="logo-img">
          <img src="data:image/png;base64,iVBOR..." alt="Logo" class="w-12 h-12">
        </div>
      </a>
    </div> -->

    <!-- Button to Open Upload Overlay -->
    <div class="p-4">
      <button @click="openUploadOverlay" class="p-2 w-full bg-blue-500 text-white rounded-md flex items-center justify-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        <span>New</span>
      </button>
    </div>

    <!-- Navigation Links -->
    <nav class="mt-4">
      <ul class="space-y-2">
        <li>
          <router-link
            to="/"
            class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white"
            active-class="bg-gray-200 dark:bg-gray-700 text-blue-500"
            exact-active-class="bg-gray-200 dark:bg-gray-700 text-blue-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 mr-2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25c0 .621.504 1.125 1.125 1.125H8.25a.375.375 0 01.375.375v3.75l4.5-4.5H19.5a1.125 1.125 0 001.125-1.125V3.75a.375.375 0 00-.375-.375H4.125A.375.375 0 003.75 3z" />
            </svg>
            <span>My Drive</span>
          </router-link>
        </li>

        <li>
          <router-link
            to="/images"
            class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white"
            active-class="bg-gray-200 dark:bg-gray-700 text-blue-500"
            exact-active-class="bg-gray-200 dark:bg-gray-700 text-blue-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 mr-2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25m0 0H12M15.75 5.25V9m0 0H19.5M4.5 9h8.25M9 3v18m9-9v6.75a2.25 2.25 0 01-2.25 2.25H6.75a2.25 2.25 0 01-2.25-2.25V6.75A2.25 2.25 0 016.75 4.5H9" />
            </svg>
            <span>Images</span>
          </router-link>
        </li>

        <li>
          <router-link
            to="/people"
            class="flex items-center p-3 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md text-gray-800 dark:text-white"
            active-class="bg-gray-200 dark:bg-gray-700 text-blue-500"
            exact-active-class="bg-gray-200 dark:bg-gray-700 text-blue-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5 mr-2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 21V19.5a4.5 4.5 0 00-4.5-4.5h-6a4.5 4.5 0 00-4.5 4.5V21m9-10.5a3 3 0 100-6 3 3 0 000 6z" />
            </svg>
            <span>People</span>
          </router-link>
        </li>
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
/* Custom scrollbar styling */
#style-3::-webkit-scrollbar {
  width: 8px;
}

#style-3::-webkit-scrollbar-track {
  background: #f1f1f1;
}

#style-3::-webkit-scrollbar-thumb {
  background-color: #888;
  border-radius: 10px;
  border: 2px solid transparent;
}

#style-3::-webkit-scrollbar-thumb:hover {
  background-color: #555;
}
</style>
