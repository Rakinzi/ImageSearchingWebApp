<template>
  <div>
    <n-space vertical :size="24">
      <!-- Page Header -->
      <div>
        <n-text tag="h1" :depth="1" style="font-size: 28px; font-weight: 600; margin: 0;">
          Upload Images
        </n-text>
        <n-text :depth="3" style="margin-top: 8px; display: block;">
          Upload your images for processing and analysis
        </n-text>
      </div>

      <!-- Upload Component -->
      <n-card>
        <upload-component @upload-complete="handleUploadComplete" />
      </n-card>
    </n-space>
  </div>
</template>

<script setup>
import { NSpace, NText, NCard, useMessage, useNotification } from 'naive-ui'
import UploadComponent from '../components/UploadComponent.vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const message = useMessage()
const notification = useNotification()

const handleUploadComplete = (result) => {
  notification.success({
    title: 'Upload Successful',
    content: `Successfully uploaded ${result.count} images`,
    duration: 3000
  })

  // Optionally redirect to images page after upload
  setTimeout(() => {
    router.push('/images')
  }, 2000)
}
</script>
  