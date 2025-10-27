// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import './style.css';

// Stores
import { useAuthStore } from './stores/authStore.js';

console.log('🚀 [Main] Starting application...');

const pinia = createPinia();
const app = createApp(App);

app.use(router);
app.use(pinia);

console.log('🔧 [Main] Vue app configured, initializing auth...');

// Initialize auth store before mounting
const authStore = useAuthStore();
authStore.initialize()
  .then(() => {
    console.log('✅ [Main] Auth initialization completed');
  })
  .catch((error) => {
    console.error('❌ [Main] Failed to initialize auth store:', error);
  })
  .finally(() => {
    console.log('🎨 [Main] Mounting Vue app...');
    app.mount('#app');
    console.log('✅ [Main] Vue app mounted successfully');
  });
