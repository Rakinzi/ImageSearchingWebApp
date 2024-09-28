// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import './style.css'
import router from './router'; // Import router
import { createPinia } from 'pinia';

const pinia = createPinia();

createApp(App)
  .use(router) // Use router
  .use(pinia) // Use Pinia
  .mount('#app');
