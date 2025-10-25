<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-3xl font-bold tracking-tight">Upload Images</h1>
      <p class="text-muted-foreground mt-1">Upload your images for processing and analysis</p>
    </div>

    <!-- Upload Component -->
    <Card>
      <CardContent class="p-6">
        <upload-component @upload-complete="handleUploadComplete" />
      </CardContent>
    </Card>
  </div>
</template>

<script setup>
import { Card, CardContent } from '@/components/ui/card'
import UploadComponent from '../components/UploadComponent.vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const handleUploadComplete = (result) => {
  alert(`Successfully uploaded ${result.count} images`)

  // Optionally redirect to images page after upload
  setTimeout(() => {
    router.push('/images')
  }, 2000)
}
</script>
