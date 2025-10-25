<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div class="flex justify-between items-center pb-6 border-b">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p class="text-muted-foreground mt-1">Welcome to your image management dashboard</p>
      </div>
      <Button @click="refreshData" variant="outline">
        <RefreshCcw class="mr-2 h-4 w-4" />
        Refresh
      </Button>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Total Images</p>
              <p class="text-3xl font-bold mt-2">{{ imageStats.total || 0 }}</p>
              <p class="text-xs text-muted-foreground mt-1">images</p>
            </div>
            <div class="h-12 w-12 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
              <Images class="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Processing</p>
              <p class="text-3xl font-bold mt-2">{{ processingCount || 0 }}</p>
              <p class="text-xs text-muted-foreground mt-1">pending</p>
            </div>
            <div class="h-12 w-12 bg-amber-100 dark:bg-amber-900 rounded-full flex items-center justify-center">
              <Clock class="h-6 w-6 text-amber-600 dark:text-amber-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Faces Detected</p>
              <p class="text-3xl font-bold mt-2">{{ faceStats.total || 0 }}</p>
              <p class="text-xs text-muted-foreground mt-1">faces</p>
            </div>
            <div class="h-12 w-12 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
              <Users class="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Storage Used</p>
              <p class="text-3xl font-bold mt-2">{{ formatFileSize(storageUsed) }}</p>
              <p class="text-xs text-muted-foreground mt-1">total</p>
            </div>
            <div class="h-12 w-12 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
              <FolderOpen class="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Recent Activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent Images -->
      <Card>
        <CardContent class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">Recent Images</h3>
            <Button variant="ghost" size="sm" @click="$router.push('/images')">
              View All
            </Button>
          </div>

          <div v-if="recentImages.length > 0" class="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div
              v-for="image in recentImages"
              :key="image.id"
              class="relative group cursor-pointer"
            >
              <img
                :src="image.thumbnail_path"
                :alt="image.original_filename"
                class="w-full aspect-square object-cover rounded-lg"
              />
              <Badge
                :variant="getStatusVariant(image.status)"
                class="absolute top-2 right-2"
              >
                {{ image.status }}
              </Badge>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-8 text-center">
            <Upload class="h-12 w-12 text-muted-foreground/30 mb-3" />
            <p class="text-muted-foreground mb-4">No recent images</p>
            <Button @click="$router.push('/upload')">Upload Images</Button>
          </div>
        </CardContent>
      </Card>

      <!-- Recent Faces -->
      <Card>
        <CardContent class="p-6">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">Recent Faces</h3>
            <Button variant="ghost" size="sm" @click="$router.push('/faces')">
              View All
            </Button>
          </div>

          <div v-if="recentFaces.length > 0" class="grid grid-cols-4 gap-3">
            <div
              v-for="face in recentFaces"
              :key="face.id"
              class="aspect-square rounded-lg overflow-hidden cursor-pointer hover:opacity-80 transition-opacity"
              @click="viewFace(face.id)"
            >
              <img
                :src="face.face_path"
                alt="Face"
                class="w-full h-full object-cover"
              />
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center py-8 text-center">
            <Users class="h-12 w-12 text-muted-foreground/30 mb-3" />
            <p class="text-muted-foreground">No faces detected yet</p>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Quick Actions -->
    <Card>
      <CardContent class="p-6">
        <h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
        <div class="flex gap-3 flex-wrap">
          <Button @click="$router.push('/upload')" size="lg">
            <Upload class="mr-2 h-5 w-5" />
            Upload Images
          </Button>
          <Button @click="$router.push('/search')" variant="outline" size="lg">
            <Search class="mr-2 h-5 w-5" />
            Search Images
          </Button>
          <Button @click="$router.push('/faces')" variant="outline" size="lg">
            <Users class="mr-2 h-5 w-5" />
            Browse Faces
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Images, Clock, Users, FolderOpen, RefreshCcw, Upload, Search } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useImagesStore } from '../stores/imagesStore.js'
import { useFaceStore } from '../stores/FaceStore.js'
import { API_BASE_URL } from '../services/api'

const router = useRouter()
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
    recentImages.value = imagesStore.images.slice(0, 5).map(image => ({
      id: image.id,
      thumbnail_path: `${API_BASE_URL}/api/v2/images/${image.id}/thumbnail`,
      original_filename: image.filename || image.original_filename || 'Untitled',
      created_at: image.created_at,
      status: image.status,
      file_size: image.file_size
    }))

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
    alert('Failed to load dashboard data')

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
  alert('Dashboard data refreshed')
}

const viewFace = (faceId) => {
  router.push(`/faces/${faceId}`)
}

// Utility methods
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const getStatusVariant = (status) => {
  switch (status) {
    case 'completed': return 'default'
    case 'processing': return 'secondary'
    case 'failed': return 'destructive'
    case 'pending': return 'outline'
    default: return 'outline'
  }
}
</script>
