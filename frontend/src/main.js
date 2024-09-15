// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import './style.css'
import router from './router'; // Import router

createApp(App)
  .use(router) // Use router
  .mount('#app');
