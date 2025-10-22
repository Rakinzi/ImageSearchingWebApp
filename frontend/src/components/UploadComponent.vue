<template>
  <div>
    <n-upload
      multiple
      directory-dnd
      :max="10"
      :default-file-list="fileList"
      :custom-request="customRequest"
      accept="image/*"
      @change="handleChange"
      @remove="handleRemove"
    >
      <n-upload-dragger>
        <div style="margin-bottom: 12px">
          <n-icon size="48" :depth="3">
            <cloud-upload />
          </n-icon>
        </div>
        <n-text style="font-size: 16px">
          Click or drag images here to upload
        </n-text>
        <n-p depth="3" style="margin: 8px 0 0 0">
          Support PNG, JPG, GIF, WEBP formats. Maximum 10 files.
        </n-p>
      </n-upload-dragger>
    </n-upload>

    <n-divider />

    <!-- Upload Options -->
    <n-space vertical>
      <n-text strong>Processing Options</n-text>
      <n-checkbox v-model:checked="options.extractText">
        Extract text from images (OCR)
      </n-checkbox>
      <n-checkbox v-model:checked="options.detectFaces">
        Detect faces in images
      </n-checkbox>
      <n-checkbox v-model:checked="options.generateEmbeddings">
        Generate AI embeddings for search
      </n-checkbox>
    </n-space>

    <n-divider />

    <!-- Metadata Input -->
    <n-form :model="metadata" label-placement="left" label-width="120px">
      <n-form-item label="Tags">
        <n-dynamic-tags v-model:value="metadata.tags" />
      </n-form-item>
      <n-form-item label="Description">
        <n-input
          v-model:value="metadata.description"
          type="textarea"
          :rows="3"
          placeholder="Optional description for these images"
        />
      </n-form-item>
      <n-form-item label="Location">
        <n-input
          v-model:value="metadata.location"
          placeholder="e.g., Paris, France"
        />
      </n-form-item>
    </n-form>

    <!-- Progress -->
    <div v-if="uploading">
      <n-divider />
      <n-progress
        type="line"
        :percentage="uploadProgress"
        :status="uploadProgress === 100 ? 'success' : 'default'"
      />
      <n-text depth="3" style="margin-top: 8px; display: block">
        {{ uploadStatus }}
      </n-text>
    </div>

    <!-- Action Buttons -->
    <n-divider />
    <n-space justify="end">
      <n-button @click="$emit('close')" :disabled="uploading">
        Cancel
      </n-button>
      <n-button
        type="primary"
        @click="startUpload"
        :disabled="fileList.length === 0 || uploading"
        :loading="uploading"
      >
        Upload {{ fileList.length }} {{ fileList.length === 1 ? 'Image' : 'Images' }}
      </n-button>
    </n-space>
  </div>
</template>

<script setup>
import { ref, reactive, watchEffect } from 'vue'
import {
  NUpload,
  NUploadDragger,
  NIcon,
  NText,
  NP,
  NDivider,
  NSpace,
  NCheckbox,
  NForm,
  NFormItem,
  NInput,
  NDynamicTags,
  NProgress,
  NButton,
  useMessage,
  useNotification
} from 'naive-ui'
import { CloudUpload } from '@vicons/ionicons5'
import { useImagesStore } from '../stores/imagesStore.js'

const emit = defineEmits(['close', 'upload-complete'])

// Composables
const message = useMessage()
const notification = useNotification()
const imagesStore = useImagesStore()

// Reactive state
const fileList = ref([])
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')

// Upload options
const options = reactive({
  extractText: true,
  detectFaces: true,
  generateEmbeddings: true
})

// Metadata
const metadata = reactive({
  tags: [],
  description: '',
  location: ''
})

// File handling
const handleChange = (data) => {
  fileList.value = data.fileList
}

const handleRemove = (data) => {
  return true // Allow removal
}

const customRequest = ({ file, onFinish, onError, onProgress }) => {
  // We'll handle the actual upload in startUpload
  // This just prevents automatic upload
  onFinish()
}

// Upload functionality
const startUpload = async () => {
  if (fileList.value.length === 0) {
    message.warning('Please select at least one image')
    return
  }

  uploading.value = true

  try {
    uploadStatus.value = 'Preparing upload...'

    // Prepare files array
    const files = fileList.value.map(fileItem => fileItem.file)

    // Prepare upload options
    const uploadOptions = {
      extractText: options.extractText,
      detectFaces: options.detectFaces,
      generateEmbeddings: options.generateEmbeddings,
      metadata: {
        tags: metadata.tags,
        description: metadata.description,
        location: metadata.location,
        upload_date: new Date().toISOString()
      }
    }

    // Use the images store to upload
    const uploadedImages = await imagesStore.uploadImages(files, uploadOptions)

    // Update progress from store
    uploadProgress.value = imagesStore.uploadProgress
    uploadStatus.value = 'Upload completed successfully!'

    // Emit success event
    emit('upload-complete', {
      count: uploadedImages.length,
      data: uploadedImages
    })

    message.success(`Successfully uploaded ${uploadedImages.length} images`)

    // Reset form
    setTimeout(() => {
      resetForm()
    }, 1000)

  } catch (error) {
    console.error('Upload failed:', error)

    uploadStatus.value = 'Upload failed'
    uploadProgress.value = 0

    message.error(error.message || 'Failed to upload images')
    notification.error({
      title: 'Upload Failed',
      content: error.message || 'Failed to upload images',
      duration: 5000
    })
  } finally {
    uploading.value = false
  }
}

const resetForm = () => {
  fileList.value = []
  uploadProgress.value = 0
  uploadStatus.value = ''
  metadata.tags = []
  metadata.description = ''
  metadata.location = ''
}

// Watch for upload progress from store
watchEffect(() => {
  if (imagesStore.uploading) {
    uploadProgress.value = imagesStore.uploadProgress
  }
})
</script>

<style scoped>
/* Naive UI handles most styling, minimal custom styles needed */
</style>