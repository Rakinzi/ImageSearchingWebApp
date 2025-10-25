<template>
  <div class="min-h-screen bg-background">
    <!-- Auth Routes (Login/Register) -->
    <div v-if="isAuthRoute" class="min-h-screen">
      <router-view />
    </div>

    <!-- Authenticated Layout with Sidebar -->
    <div v-else-if="authStore.isAuthenticated" class="flex h-screen">
      <!-- Sidebar -->
      <aside :class="['bg-card border-r transition-all duration-300', sidebarCollapsed ? 'w-16' : 'w-64']">
        <div class="flex flex-col h-full">
          <!-- Logo/Brand -->
          <div class="p-4 border-b">
            <h2 v-if="!sidebarCollapsed" class="text-xl font-bold">Image Search</h2>
            <div v-else class="flex justify-center">
              <Images class="h-6 w-6" />
            </div>
          </div>

          <!-- Navigation Menu -->
          <nav class="flex-1 p-4 space-y-2">
            <button
              v-for="item in menuItems"
              :key="item.key"
              @click="handleMenuSelect(item.key)"
              :class="[
                'w-full flex items-center gap-3 px-3 py-2 rounded-md transition-colors',
                activeKey === item.key
                  ? 'bg-primary text-primary-foreground'
                  : 'hover:bg-muted'
              ]"
            >
              <component :is="item.icon" class="h-5 w-5 flex-shrink-0" />
              <span v-if="!sidebarCollapsed" class="text-sm font-medium">{{ item.label }}</span>
            </button>
          </nav>

          <!-- Sidebar Toggle -->
          <div class="p-4 border-t">
            <Button
              @click="sidebarCollapsed = !sidebarCollapsed"
              variant="ghost"
              size="sm"
              class="w-full"
            >
              <Menu class="h-4 w-4" />
              <span v-if="!sidebarCollapsed" class="ml-2">Collapse</span>
            </Button>
          </div>
        </div>
      </aside>

      <!-- Main Content Area -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- Header -->
        <header class="h-16 border-b bg-card px-6 flex items-center justify-between">
          <h1 class="text-lg font-semibold">Image Search App</h1>

          <div class="flex items-center gap-3">
            <!-- Upload Button -->
            <Button @click="showUploadDialog = true">
              <Upload class="mr-2 h-4 w-4" />
              Upload Images
            </Button>

            <!-- Theme Toggle -->
            <Button @click="toggleTheme" variant="outline" size="icon">
              <Sun v-if="isDark" class="h-5 w-5" />
              <Moon v-else class="h-5 w-5" />
            </Button>

            <!-- User Menu -->
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <Button variant="outline" size="icon">
                  <User class="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem @click="$router.push('/profile')">
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem @click="$router.push('/settings')">
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem @click="handleLogout">
                  <LogOut class="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <!-- Content -->
        <main class="flex-1 overflow-auto p-6">
          <router-view />
        </main>
      </div>
    </div>

    <!-- Upload Dialog -->
    <Dialog v-model:open="showUploadDialog">
      <DialogContent class="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Images</DialogTitle>
        </DialogHeader>
        <upload-component @upload-complete="handleUploadComplete" @close="showUploadDialog = false" />
      </DialogContent>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Home, Images, Users, Upload, Settings, User, LogOut, Sun, Moon, Menu } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from './stores/authStore'
import UploadComponent from './components/UploadComponent.vue'

// Stores and composables
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

// Reactive state
const sidebarCollapsed = ref(false)
const showUploadDialog = ref(false)
const activeKey = ref(null)
const isDark = ref(false)

// Computed properties
const isAuthRoute = computed(() => {
  const authRoutes = ['/login', '/register', '/forgot-password', '/verify-email']
  return authRoutes.includes(route.path) || route.path.startsWith('/verify-email')
})

// Menu items
const menuItems = [
  { key: 'dashboard', label: 'Dashboard', icon: Home },
  { key: 'images', label: 'Images', icon: Images },
  { key: 'people', label: 'People', icon: Users },
  { key: 'upload', label: 'Upload', icon: Upload },
]

// Set active menu key based on current route
const setActiveKey = () => {
  const path = route.path
  if (path === '/') {
    activeKey.value = 'dashboard'
  } else if (path === '/images') {
    activeKey.value = 'images'
  } else if (path === '/people' || path.startsWith('/faces')) {
    activeKey.value = 'people'
  } else if (path === '/upload') {
    activeKey.value = 'upload'
  } else {
    activeKey.value = null
  }
}

// Watch route changes to update active menu item
watch(route, setActiveKey, { immediate: true })

// Event handlers
const handleMenuSelect = (key) => {
  activeKey.value = key

  // Handle special routing cases
  if (key === 'dashboard') {
    router.push('/')
  } else {
    router.push(`/${key}`)
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  console.log('Theme toggled:', isDark.value, 'HTML classes:', document.documentElement.className)
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleUploadComplete = (result) => {
  showUploadDialog.value = false
  alert(`Successfully uploaded ${result.count} images`)
}

// Initialize theme from localStorage
const savedTheme = localStorage.getItem('theme')
if (savedTheme === 'dark') {
  isDark.value = true
  document.documentElement.classList.add('dark')
} else {
  isDark.value = false
  document.documentElement.classList.remove('dark')
}
</script>
