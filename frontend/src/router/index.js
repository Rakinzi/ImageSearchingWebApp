// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import Files from '../views/Files.vue';
import Upload from '../views/Upload.vue';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/files',
    name: 'Files',
    component: Files
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload
  },
  { path: '/login', name: 'Login', component: Login, meta: { layout: 'auth' } },
  { path: '/register', name: 'Register', component: Register, meta: { layout: 'auth' } },
];

const router = createRouter({
  history: createWebHistory('/'),
  routes
});

export default router;
