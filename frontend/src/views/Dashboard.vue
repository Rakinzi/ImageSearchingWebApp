<template>
  <div>
    <!-- Page Header -->
    <n-page-header title="Dashboard" subtitle="Welcome to your image management dashboard">
      <template #extra>
        <n-space>
          <n-button type="primary" @click="refreshData">
            <template #icon>
              <n-icon><refresh /></n-icon>
            </template>
            Refresh
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-divider />

    <!-- Stats Grid -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen">
      <n-grid-item>
        <n-card title="Total Images" size="small">
          <template #header-extra>
            <n-icon size="20" color="#3B82F6"><images-icon /></n-icon>
          </template>
          <n-statistic :value="imageStats.total || 0">
            <template #suffix>
              <n-text depth="3">images</n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card title="Processing" size="small">
          <template #header-extra>
            <n-icon size="20" color="#F59E0B"><time /></n-icon>
          </template>
          <n-statistic :value="processingCount || 0">
            <template #suffix>
              <n-text depth="3">pending</n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card title="Faces Detected" size="small">
          <template #header-extra>
            <n-icon size="20" color="#10B981"><people /></n-icon>
          </template>
          <n-statistic :value="faceStats.total || 0">
            <template #suffix>
              <n-text depth="3">faces</n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card title="Storage Used" size="small">
          <template #header-extra>
            <n-icon size="20" color="#8B5CF6"><folder /></n-icon>
          </template>
          <n-statistic :value="formatFileSize(storageUsed)">
            <template #suffix>
              <n-text depth="3"></n-text>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-divider />

    <!-- Recent Activity -->
    <n-grid :cols="2" :x-gap="16">
      <n-grid-item>
        <n-card title="Recent Images" size="small">
          <template #header-extra>
            <n-button text @click="$router.push('/images')">View All</n-button>
          </template>

          <n-list v-if="recentImages.length > 0">
            <n-list-item v-for="image in recentImages" :key="image.id">
              <template #prefix>
                <n-avatar
                  :src="image.thumbnail_path"
                  :fallback-src="'/placeholder-image.png'"
                  round
                  size="medium"
                />
              </template>
              <n-thing :title="image.original_filename" :description="formatDate(image.created_at)">
                <template #footer>
                  <n-space>
                    <n-tag :type="getStatusType(image.status)" size="small">
                      {{ image.status }}
                    </n-tag>
                    <n-text depth="3" style="font-size: 12px">
                      {{ formatFileSize(image.file_size) }}
                    </n-text>
                  </n-space>
                </template>
              </n-thing>
            </n-list-item>
          </n-list>

          <n-empty v-else description="No recent images">
            <template #extra>
              <n-button @click="$router.push('/upload')">Upload Images</n-button>
            </template>
          </n-empty>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card title="Recent Faces" size="small">
          <template #header-extra>
            <n-button text @click="$router.push('/faces')">View All</n-button>
          </template>

          <n-grid v-if="recentFaces.length > 0" :cols="4" :x-gap="8" :y-gap="8">
            <n-grid-item v-for="face in recentFaces" :key="face.id">
              <n-avatar
                :src="face.face_path"
                :fallback-src="'/placeholder-face.png'"
                size="large"
                style="cursor: pointer"
                @click="viewFace(face.id)"
              />
            </n-grid-item>
          </n-grid>

          <n-empty v-else description="No faces detected yet" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-divider />

    <!-- Quick Actions -->
    <n-card title="Quick Actions" size="small">
      <n-space size="large">
        <n-button type="primary" size="large" @click="$router.push('/upload')">
          <template #icon>
            <n-icon><cloud-upload /></n-icon>
          </template>
          Upload Images
        </n-button>

        <n-button size="large" @click="$router.push('/search')">
          <template #icon>
            <n-icon><search /></n-icon>
          </template>
          Search Images
        </n-button>

        <n-button size="large" @click="$router.push('/faces')">
          <template #icon>
            <n-icon><people /></n-icon>
          </template>
          Browse Faces
        </n-button>
      </n-space>
    </n-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NPageHeader,
  NDivider,
  NGrid,
  NGridItem,
  NCard,
  NStatistic,
  NIcon,
  NText,
  NButton,
  NSpace,
  NList,
  NListItem,
  NAvatar,
  NThing,
  NTag,
  NEmpty,
  useMessage
} from 'naive-ui'
import {
  Images as ImagesIcon,
  Time,
  People,
  Folder,
  Refresh,
  CloudUpload,
  Search
} from '@vicons/ionicons5'
import dayjs from 'dayjs'
import { useImagesStore } from '../stores/imagesStore.js'
import { useFaceStore } from '../stores/FaceStore.js'

const router = useRouter()
const message = useMessage()
const imagesStore = useImagesStore()
const faceStore = useFaceStore()

// Reactive state
const imageStats = ref({ total: 0 })
const faceStats = ref({ total: 0 })
const processingCount = ref(0)
const storageUsed = ref(0)
const recentImages = ref([])
const recentFaces = ref([])

// Lifecycle
onMounted(() => {
  loadDashboardData()
})

// Methods
const loadDashboardData = async () => {
  try {
    // Load image statistics
    await imagesStore.loadStats()
    imageStats.value = { total: imagesStore.stats.totalImages }
    faceStats.value = { total: imagesStore.stats.withFaces }
    processingCount.value = imagesStore.stats.processing
    storageUsed.value = imagesStore.stats.totalSize

    // Load recent images
    await imagesStore.loadImages(1, true)
    recentImages.value = imagesStore.images.slice(0, 5)

    // Load recent faces if available
    try {
      if (faceStore.loadFaceData) {
        await faceStore.loadFaceData()
        recentFaces.value = (faceStore.faceData?.faces || []).slice(0, 8)
      }
    } catch (faceError) {
      console.warn('Could not load face data:', faceError)
      recentFaces.value = []
    }

  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    message.error('Failed to load dashboard data')

    // Fallback to mock data if API fails
    imageStats.value = { total: 0 }
    faceStats.value = { total: 0 }
    processingCount.value = 0
    storageUsed.value = 0
    recentImages.value = []
    recentFaces.value = []
  }
}

const refreshData = () => {
  loadDashboardData()
  message.success('Dashboard data refreshed')
}

const viewFace = (faceId) => {
  router.push(`/faces/${faceId}`)
}

// Utility methods
const formatDate = (dateString) => {
  return dayjs(dateString).format('MMM D, YYYY h:mm A')
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getStatusType = (status) => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'info'
    case 'failed': return 'error'
    case 'pending': return 'warning'
    default: return 'default'
  }
}
</script>

<style scoped>
/* Minimal custom styles - Naive UI handles most styling */
</style>