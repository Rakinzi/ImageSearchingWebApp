<template>
  <div class="space-y-6">
    <!-- Drag and Drop Area -->
    <div
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      :class="[
        'border-2 border-dashed rounded-lg p-12 text-center transition-colors',
        isDragging ? 'border-primary bg-primary/5' : 'border-muted-foreground/25 hover:border-primary/50'
      ]"
    >
      <Upload class="h-12 w-12 mx-auto mb-3 text-muted-foreground" />
      <p class="text-base font-medium mb-2">Click or drag images here to upload</p>
      <p class="text-sm text-muted-foreground">Support PNG, JPG, GIF, WEBP formats. Maximum 10 files.</p>
      <input
        ref="fileInput"
        type="file"
        multiple
        accept="image/*"
        class="hidden"
        @change="handleFileSelect"
      />
      <Button @click="$refs.fileInput.click()" class="mt-4" variant="outline">
        Select Files
      </Button>
    </div>

    <!-- File List -->
    <div v-if="fileList.length > 0" class="space-y-2">
      <h3 class="font-semibold">Selected Files ({{ fileList.length }})</h3>
      <div class="space-y-2">
        <div
          v-for="(file, index) in fileList"
          :key="index"
          class="flex items-center justify-between p-3 bg-muted rounded-lg"
        >
          <div class="flex items-center gap-3">
            <FileImage class="h-5 w-5 text-muted-foreground" />
            <span class="text-sm">{{ file.name }}</span>
          </div>
          <Button variant="ghost" size="sm" @click="removeFile(index)">
            <X class="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>

    <Separator />

    <!-- Processing Options -->
    <div class="space-y-4">
      <div>
        <h3 class="font-semibold text-base">Processing Options</h3>
        <p class="text-sm text-muted-foreground mt-1">Select which AI features to apply to your images</p>
      </div>

      <Card class="bg-muted/30">
        <CardContent class="p-4 space-y-4">
          <!-- OCR Option -->
          <div class="flex items-start space-x-3">
            <Checkbox id="ocr" v-model:checked="options.extractText" class="mt-1" />
            <div class="flex-1">
              <Label for="ocr" class="font-medium cursor-pointer flex items-center gap-2">
                <FileText class="h-4 w-4" />
                Extract Text (OCR)
              </Label>
              <p class="text-xs text-muted-foreground mt-1">
                Detect and extract text from images using optical character recognition
              </p>
            </div>
          </div>

          <!-- Face Detection Option -->
          <div class="flex items-start space-x-3">
            <Checkbox id="faces" v-model:checked="options.detectFaces" class="mt-1" />
            <div class="flex-1">
              <Label for="faces" class="font-medium cursor-pointer flex items-center gap-2">
                <User class="h-4 w-4" />
                Detect Faces
              </Label>
              <p class="text-xs text-muted-foreground mt-1">
                Identify and analyze faces with age, gender, and emotion detection
              </p>
            </div>
          </div>

          <!-- Embeddings (Always Enabled - System Core Feature) -->
          <div class="flex items-start space-x-3 opacity-60">
            <Checkbox id="embeddings" checked disabled class="mt-1" />
            <div class="flex-1">
              <Label for="embeddings" class="font-medium flex items-center gap-2">
                <Search class="h-4 w-4" />
                Generate AI Embeddings
                <Badge variant="outline" class="ml-2">Always On</Badge>
              </Label>
              <p class="text-xs text-muted-foreground mt-1">
                AI embeddings are always generated for semantic search and similarity matching
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

    </div>

    <Separator />

    <!-- Metadata Input -->
    <div class="space-y-4">
      <h3 class="font-semibold">Optional Metadata</h3>

      <div class="space-y-2">
        <Label for="tags">Tags</Label>
        <Input
          id="tags"
          v-model="tagsInput"
          placeholder="Enter tags separated by commas"
          @blur="processTags"
        />
        <div v-if="metadata.tags.length > 0" class="flex gap-2 flex-wrap mt-2">
          <Badge v-for="(tag, index) in metadata.tags" :key="index" variant="secondary">
            {{ tag }}
            <button @click="removeTag(index)" class="ml-1 hover:text-destructive">
              <X class="h-3 w-3" />
            </button>
          </Badge>
        </div>
      </div>

      <div class="space-y-2">
        <Label for="description">Description</Label>
        <textarea
          id="description"
          v-model="metadata.description"
          placeholder="Optional description for these images"
          rows="3"
          class="w-full px-3 py-2 text-sm rounded-md border border-input bg-background"
        />
      </div>

      <div class="space-y-2">
        <Label for="location">Location</Label>
        <Input
          id="location"
          v-model="metadata.location"
          placeholder="e.g., Paris, France"
        />
      </div>
    </div>

    <!-- Progress -->
    <div v-if="uploading" class="space-y-2">
      <Separator />
      <div class="w-full bg-muted rounded-full h-2">
        <div
          class="bg-primary h-2 rounded-full transition-all duration-300"
          :style="{ width: `${uploadProgress}%` }"
        ></div>
      </div>
      <p class="text-sm text-muted-foreground">{{ uploadStatus }}</p>
    </div>

    <!-- Action Buttons -->
    <Separator />
    <div class="flex justify-end gap-3">
      <Button @click="$emit('close')" :disabled="uploading" variant="outline">
        Cancel
      </Button>
      <Button
        @click="startUpload"
        :disabled="fileList.length === 0 || uploading"
      >
        <span v-if="uploading" class="flex items-center">
          <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
          Uploading...
        </span>
        <span v-else>
          Upload {{ fileList.length }} {{ fileList.length === 1 ? 'Image' : 'Images' }}
        </span>
      </Button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { Upload, FileImage, X, FileText, User, Search } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { toast } from 'vue-sonner'
import { useImagesStore } from '../stores/imagesStore.js'

const emit = defineEmits(['close', 'upload-complete'])

// Composables
const imagesStore = useImagesStore()

// Reactive state
const fileInput = ref(null)
const fileList = ref([])
const isDragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const tagsInput = ref('')

// Upload options
const options = reactive({
  extractText: true,
  detectFaces: true,
  // generateEmbeddings is always true - removed from UI
})

// Metadata
const metadata = reactive({
  tags: [],
  description: '',
  location: ''
})

// File handling
const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  addFiles(files)
}

const handleDrop = (event) => {
  isDragging.value = false
  const files = Array.from(event.dataTransfer.files).filter(file => file.type.startsWith('image/'))
  addFiles(files)
}

const addFiles = (files) => {
  const newFiles = files.slice(0, 10 - fileList.value.length)
  fileList.value.push(...newFiles)
  if (fileList.value.length > 10) {
    fileList.value = fileList.value.slice(0, 10)
    toast.warning('Maximum 10 files allowed', {
      description: 'Only the first 10 files will be uploaded'
    })
  }
}

const removeFile = (index) => {
  fileList.value.splice(index, 1)
}

const processTags = () => {
  if (tagsInput.value.trim()) {
    const newTags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t)
    metadata.tags = [...new Set([...metadata.tags, ...newTags])]
    tagsInput.value = ''
  }
}

const removeTag = (index) => {
  metadata.tags.splice(index, 1)
}

// Upload functionality
const startUpload = async () => {
  if (fileList.value.length === 0) {
    toast.error('No images selected', {
      description: 'Please select at least one image to upload'
    })
    return
  }

  uploading.value = true

  try {
    uploadStatus.value = 'Preparing upload...'

    // Prepare upload options
    const uploadOptions = {
      extractText: options.extractText,
      detectFaces: options.detectFaces,
      generateEmbeddings: true, // Always generate embeddings - core system feature
      metadata: {
        tags: metadata.tags,
        description: metadata.description,
        location: metadata.location,
        upload_date: new Date().toISOString()
      }
    }

    // Use the images store to upload
    const uploadedImages = await imagesStore.uploadImages(fileList.value, uploadOptions)

    // Update progress from store
    uploadProgress.value = 100
    uploadStatus.value = 'Upload completed successfully!'

    // Emit success event
    emit('upload-complete', {
      count: uploadedImages.length,
      data: uploadedImages
    })

    toast.success('Upload successful!', {
      description: `Successfully uploaded ${uploadedImages.length} ${uploadedImages.length === 1 ? 'image' : 'images'}. AI processing started in background.`
    })

    // Reset form
    setTimeout(() => {
      resetForm()
    }, 1000)

  } catch (error) {
    console.error('Upload failed:', error)

    uploadStatus.value = 'Upload failed'
    uploadProgress.value = 0

    toast.error('Upload failed', {
      description: error.message || 'Failed to upload images. Please try again.'
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
  tagsInput.value = ''
}

// Watch for upload progress from store
watch(() => imagesStore.uploading, (newVal) => {
  if (newVal) {
    uploadProgress.value = imagesStore.uploadProgress
  }
})
</script>
