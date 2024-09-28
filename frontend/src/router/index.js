// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Dashboard from '../views/Dashboard.vue';
import People from '../views/People.vue';
import Upload from '../views/Upload.vue';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import RelatedFaces from '../views/RelatedFaces.vue';
import { auth } from '../services/firebase'; // Import Firebase Auth instance


const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    // meta: { requiresAuth: true }
  },
  {
    path: '/people',
    name: 'People',
    component: People,
    // meta: { requiresAuth: true }
  },
  {
    path: '/faces/:faceId',
    name: 'RelatedFaces',
    component: RelatedFaces
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    meta: { requiresAuth: true }
  },
  { path: '/login', name: 'Login', component: Login, meta: { layout: 'auth' } },
  { path: '/register', name: 'Register', component: Register, meta: { layout: 'auth' } },
];

const router = createRouter({
  history: createWebHistory('/'),
  routes
});

// Navigation guard to protect routes that require authentication
router.beforeEach((to, from, next) => {
  // Get the currently authenticated user
  const currentUser = auth.currentUser;

  // Check if the route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // If not logged in, redirect to login page
    if (!currentUser) {
      next('/login');
    } else {
      next(); // Proceed if the user is authenticated
    }
  } else {
    next(); // Proceed to route if it does not require authentication
  }
});


export default router;
