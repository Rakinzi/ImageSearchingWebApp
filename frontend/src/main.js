// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import './style.css';

// Stores
import { useAuthStore } from './stores/authStore.js';

const pinia = createPinia();
const app = createApp(App);

app.use(router);
app.use(pinia);

// Initialize auth store
const authStore = useAuthStore();
authStore.initialize();

app.mount('#app');
