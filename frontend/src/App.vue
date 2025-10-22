<template>
  <n-config-provider :theme="isDark ? darkTheme : null" :theme-overrides="themeOverrides">
    <n-global-style />
    <n-message-provider>
      <n-dialog-provider>
        <n-notification-provider>
          <n-loading-bar-provider>
            <div class="app-container">
              <n-layout has-sider v-if="authStore.isAuthenticated && !isAuthRoute" style="height: 100vh;">
                <!-- Sidebar Navigation -->
                <n-layout-sider
                  bordered
                  collapse-mode="width"
                  :collapsed-width="64"
                  :width="240"
                  :collapsed="collapsed"
                  show-trigger
                  @collapse="collapsed = true"
                  @expand="collapsed = false"
                  style="height: 100vh;"
                >
                  <n-menu
                    v-model:value="activeKey"
                    :collapsed="collapsed"
                    :collapsed-width="64"
                    :collapsed-icon-size="22"
                    :options="menuOptions"
                    @update:value="handleMenuSelect"
                  />
                </n-layout-sider>

                <!-- Main Content Area -->
                <n-layout>
                  <!-- Header -->
                  <n-layout-header bordered style="height: 64px; padding: 0 24px">
                    <n-space justify="space-between" align="center" style="height: 100%">
                      <n-text strong style="font-size: 18px">Image Search App</n-text>

                      <n-space align="center">
                        <!-- Upload Button -->
                        <n-button
                          type="primary"
                          @click="showUploadModal = true"
                        >
                          <template #icon>
                            <n-icon><cloud-upload /></n-icon>
                          </template>
                          Upload Images
                        </n-button>

                        <!-- Theme Toggle -->
                        <n-button
                          quaternary
                          circle
                          @click="toggleTheme"
                        >
                          <template #icon>
                            <n-icon><sunny v-if="isDark" /><moon v-else /></n-icon>
                          </template>
                        </n-button>

                        <!-- User Menu -->
                        <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
                          <n-button quaternary circle>
                            <template #icon>
                              <n-icon><person /></n-icon>
                            </template>
                          </n-button>
                        </n-dropdown>
                      </n-space>
                    </n-space>
                  </n-layout-header>

                  <!-- Content -->
                  <n-layout-content content-style="padding: 24px">
                    <router-view />
                  </n-layout-content>
                </n-layout>
              </n-layout>

              <!-- Auth Routes (Login/Register) -->
              <div v-else class="auth-container">
                <router-view />
              </div>

              <!-- Upload Modal -->
              <n-modal v-model:show="showUploadModal" preset="card" title="Upload Images" style="width: 600px">
                <upload-component @upload-complete="handleUploadComplete" />
              </n-modal>
            </div>
          </n-loading-bar-provider>
        </n-notification-provider>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, h, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  darkTheme,
  NConfigProvider,
  NGlobalStyle,
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider,
  NLoadingBarProvider,
  NLayout,
  NLayoutSider,
  NLayoutHeader,
  NLayoutContent,
  NMenu,
  NButton,
  NSpace,
  NText,
  NIcon,
  NDropdown,
  NModal,
  useMessage,
  useNotification
} from 'naive-ui'
import {
  Home,
  Images,
  People,
  Search,
  Settings,
  CloudUpload,
  Person,
  LogOut,
  Sunny,
  Moon
} from '@vicons/ionicons5'
import { useAuthStore } from './stores/authStore'
import UploadComponent from './components/UploadComponent.vue'

// Stores and composables
const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

// Reactive state
const collapsed = ref(false)
const showUploadModal = ref(false)
const activeKey = ref(null)
const isDark = ref(false)

// Theme configuration
const themeOverrides = {
  common: {
    primaryColor: '#3B82F6',
    primaryColorHover: '#2563EB',
    primaryColorPressed: '#1D4ED8',
  }
}

// Computed properties
const isAuthRoute = computed(() => {
  const authRoutes = ['/login', '/register', '/forgot-password']
  return authRoutes.includes(route.path)
})

// Set active menu key based on current route
const setActiveKey = () => {
  const path = route.path
  if (path === '/') {
    activeKey.value = 'dashboard'
  } else if (path === '/images') {
    activeKey.value = 'images'
  } else if (path === '/people') {
    activeKey.value = 'people'
  } else if (path === '/upload') {
    activeKey.value = 'upload'
  } else {
    activeKey.value = null
  }
}

// Watch route changes to update active menu item
watch(route, setActiveKey, { immediate: true })

// Menu configuration
const menuOptions = [
  {
    label: 'Dashboard',
    key: 'dashboard',
    icon: () => h(NIcon, null, { default: () => h(Home) })
  },
  {
    label: 'Images',
    key: 'images',
    icon: () => h(NIcon, null, { default: () => h(Images) })
  },
  {
    label: 'People',
    key: 'people',
    icon: () => h(NIcon, null, { default: () => h(People) })
  },
  {
    label: 'Upload',
    key: 'upload',
    icon: () => h(NIcon, null, { default: () => h(CloudUpload) })
  }
]

const userMenuOptions = [
  {
    label: 'Profile',
    key: 'profile'
  },
  {
    label: 'Settings',
    key: 'settings'
  },
  {
    type: 'divider'
  },
  {
    label: 'Logout',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOut) })
  }
]

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

const handleUserMenuSelect = (key) => {
  const message = useMessage()

  switch (key) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      authStore.logout()
      router.push('/login')
      message.success('Logged out successfully')
      break
  }
}

const toggleTheme = () => {
  isDark.value = !isDark.value
  // You can persist this to localStorage
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const handleUploadComplete = (result) => {
  const notification = useNotification()

  showUploadModal.value = false
  notification.success({
    title: 'Upload Complete',
    content: `Successfully uploaded ${result.count} images`,
    duration: 3000
  })
}

// Initialize theme from localStorage
const savedTheme = localStorage.getItem('theme')
if (savedTheme) {
  isDark.value = savedTheme === 'dark'
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.auth-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>