<template>
  <div>
    <!-- If loading, show a spinner -->
    <div v-if="loading" class="flex justify-center items-center h-screen">
      <div class="spinner"></div> <!-- You can replace this with any spinner component -->
    </div>

    <!-- If not loading, show the app layout -->
    <div v-else class="flex h-screen">
      <!-- Conditionally render SideNav and Navbar based on authentication -->
      <SideNav 
        v-if="isAuthenticated && !isAuthRoute" 
        @openUploadOverlay="showOverlay = true" 
        class="fixed top-0 left-0 h-full w-64 bg-gray-200 dark:bg-gray-800"
      />
      <div class="flex-1 flex flex-col ml-64"> <!-- Adjust left margin to accommodate SideNav width -->
        <Navbar 
          v-if="isAuthenticated && !isAuthRoute" 
          class="fixed top-0 left-64 right-0 bg-white dark:bg-gray-900 shadow-md"
        />
        <main class="flex-1 p-4 mt-16 bg-gray-100 dark:bg-gray-900"> <!-- Add top margin to account for Navbar height -->
          <router-view />
        </main>
      </div>
    </div>
    <FileUploadOverlay :showOverlay="showOverlay" @close="showOverlay = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from './services/firebase';
import SideNav from './components/SideNav.vue';
import Navbar from './components/NavBar.vue';
// import router from './router/index';
import { useRoute } from 'vue-router';  // Import useRoute to access current path
import FileUploadOverlay from './components/FileUploadOverlay.vue';

const showOverlay = ref(false);

// Reactive properties
const loading = ref(true);
const isAuthenticated = ref(false);

const route = useRoute(); // Get the current route

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

// Computed property to determine if the current route is `/login` or `/register`
const isAuthRoute = computed(() => {
  return route.path === '/login' || route.path === '/register';
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

/* Ensure that the Navbar and SideNav do not move */
.fixed {
  position: fixed;
}

.ml-64 {
  margin-left: 16rem; /* Adjust this value based on the width of your SideNav */
}

.mt-16 {
  margin-top: 4rem; /* Adjust this value based on the height of your Navbar */
}

.bg-gray-200 {
  background-color: #edf2f7; /* Light gray background for SideNav */
}

.bg-gray-900 {
  background-color: #1a202c; /* Dark background for Navbar */
}

.shadow-md {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Shadow for Navbar */
}

</style>
