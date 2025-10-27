// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/authStore'; // Import Pinia store
import Dashboard from '../views/Dashboard.vue';
import People from '../views/People.vue';
import Upload from '../views/Upload.vue';
import Login from '../views/Login.vue';
import Register from '../views/Register.vue';
import RelatedFaces from '../views/RelatedFaces.vue';
import Images from '../views/Images.vue';
import ImageDetail from '../views/ImageDetail.vue';
import VerifyEmail from '../views/VerifyEmail.vue';


const routes = [
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/images',
    name: 'Images',
    component: Images,
    meta: { requiresAuth: true }
  },
  {
    path: '/images/:id',
    name: 'ImageDetail',
    component: ImageDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/people',
    name: 'People',
    component: People,
    meta: { requiresAuth: true }
  },
  {
    path: '/faces/:faceId',
    name: 'RelatedFaces',
    component: RelatedFaces
  },

  { path: '/login', name: 'Login', component: Login, meta: { layout: 'auth' } },
  { path: '/register', name: 'Register', component: Register, meta: { layout: 'auth' } },
  { path: '/verify-email', name: 'verify-email', component: VerifyEmail, meta: {  layout: 'auth' } }
];

const router = createRouter({
  history: createWebHistory('/'),
  routes
});

// Navigation guard to protect routes that require authentication
router.beforeEach(async (to, from, next) => {
  console.log('🛣️ [Router Guard] Navigation:', {
    from: from.path,
    to: to.path,
    requiresAuth: to.matched.some(record => record.meta.requiresAuth)
  });

  const authStore = useAuthStore(); // Get the auth store

  console.log('🛣️ [Router Guard] Auth state:', {
    isLoggedIn: authStore.isLoggedIn,
    isAuthenticated: authStore.isAuthenticated,
    hasUser: !!authStore.user,
    loading: authStore.loading,
    initialized: authStore.initialized
  });

  // If navigating from login/register, the auth state should already be set
  const isComingFromAuth = ['/login', '/register'].includes(from.path);

  // Check if the route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    console.log('🔒 [Router Guard] Route requires authentication');

    // If coming from auth pages, we can trust the current state
    if (isComingFromAuth) {
      console.log('🔄 [Router Guard] Coming from auth page');
      if (!authStore.isLoggedIn) {
        console.log('❌ [Router Guard] Not logged in, redirecting to /login');
        next('/login');
      } else {
        console.log('✅ [Router Guard] Logged in, proceeding to', to.path);
        next();
      }
      return;
    }

    // If auth is still loading (initial load), wait for it
    if (authStore.loading) {
      console.log('⏳ [Router Guard] Auth is loading, waiting...');
      // Wait for loading to complete by polling
      const maxWait = 5000; // 5 seconds max
      const startTime = Date.now();
      while (authStore.loading && (Date.now() - startTime) < maxWait) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      console.log('✅ [Router Guard] Auth loading complete');
    }

    // For page refreshes or direct navigation, check if we need to initialize
    // If not initialized yet and no user, try to restore session
    if (!authStore.initialized && !authStore.user && !authStore.loading) {
      console.log('🔄 [Router Guard] Not initialized, attempting to initialize...');
      try {
        await authStore.initialize();

        console.log('🔄 [Router Guard] After initialization:', {
          isLoggedIn: authStore.isLoggedIn,
          hasUser: !!authStore.user
        });

        if (authStore.isLoggedIn) {
          console.log('✅ [Router Guard] Auth successful, proceeding to', to.path);
          next(); // Authentication successful, proceed
        } else {
          console.log('❌ [Router Guard] No valid session, redirecting to /login');
          next('/login'); // No valid session, redirect to login
        }
      } catch (error) {
        console.error('❌ [Router Guard] Auth check failed:', error);
        next('/login'); // Auth failed, redirect to login
      }
    } else if (authStore.isLoggedIn) {
      console.log('✅ [Router Guard] Already authenticated, proceeding to', to.path);
      next(); // Already authenticated, proceed
    } else {
      console.log('❌ [Router Guard] Not authenticated, redirecting to /login');
      next('/login'); // Not authenticated, redirect to login
    }
  } else {
    console.log('🔓 [Router Guard] Route does not require auth, proceeding to', to.path);
    // Route doesn't require auth, proceed
    next();
  }
});


export default router;
