<template>
    <div class="flex h-screen">
      <!-- Conditionally Render SideNav -->
      <SideNav v-if="!hideSideNav" />
  
      <!-- Main content area -->
      <div class="flex-1 flex flex-col">
        <!-- Conditionally Render Navbar -->
        <Navbar v-if="!hideNavbar" />
  
        <!-- Content -->
        <main class="flex-1 p-4 bg-gray-100 dark:bg-gray-900">
          <router-view />
        </main>
      </div>
    </div>
  </template>
  
  <script setup>
  import { computed } from 'vue';
  import { useRoute } from 'vue-router';
  import Navbar from './components/NavBar.vue';
  import SideNav from './components/SideNav.vue';
  
  const route = useRoute();
  
  const hideNavbar = computed(() => {
    // Hide the Navbar if the route meta layout is 'auth'
    return route.meta.layout === 'auth';
  });
  
  const hideSideNav = computed(() => {
    // Hide the SideNav if the route meta layout is 'auth'
    return route.meta.layout === 'auth';
  });
  </script>
  
  <style>
  /* Global dark mode background */
  html.dark {
    background-color: #1a202c;
  }
  </style>
  
  