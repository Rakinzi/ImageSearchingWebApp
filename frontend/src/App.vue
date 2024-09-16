<template>
  <div>

    <!-- If loading, show a spinner -->
    <div v-if="loading" class="flex justify-center items-center h-screen">
      <div class="spinner"></div> <!-- You can replace this with any spinner component -->
    </div>

    <!-- If not loading, show the app layout -->
    <div v-else class="flex h-screen">
      <!-- Conditionally render SideNav and Navbar based on authentication -->
     
      <SideNav @openUploadOverlay="showOverlay = true"   v-if="isAuthenticated"/>
      <div class="flex-1 flex flex-col">
        <Navbar v-if="isAuthenticated" />
        <main class="flex-1 p-4 bg-gray-100 dark:bg-gray-900">
          <router-view />
        </main>
      </div>
    </div>
    <FileUploadOverlay :showOverlay="showOverlay" @close="showOverlay = false" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './services/firebase';
import SideNav from './components/SideNav.vue';
import Navbar from './components/NavBar.vue';
import router from './router/index';
import FileUploadOverlay from './components/FileUploadOverlay.vue';

const showOverlay = ref(false);

// Reactive properties
const loading = ref(true);
const isAuthenticated = ref(false);

onMounted(() => {
  // Listen for changes to the user's authentication state
  onAuthStateChanged(auth, (user) => {
    if (user) {
      isAuthenticated.value = true; // User is authenticated
    } else {
      isAuthenticated.value = false; // User is not authenticated
    }
    loading.value = false; // Firebase auth state has been resolved
  });
});
</script>

<style>
/* Example CSS for spinner (can be customized or replaced) */
.spinner {
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
