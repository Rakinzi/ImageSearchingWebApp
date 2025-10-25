<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ArrowLeft, Download, Edit2, RefreshCw, MapPin, Calendar, HardDrive, Image as ImageIcon, FileText, User } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import VueEasyLightbox from 'vue-easy-lightbox';
import { apiService, API_BASE_URL } from '../services/api';

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const imageData = ref(null);
const error = ref(null);
const visibleRef = ref(false);

onMounted(async () => {
  await loadImageDetails();
});

const loadImageDetails = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await apiService.images.get(route.params.id);

    if (response.data && response.data.data) {
      imageData.value = response.data.data;
    } else {
      error.value = 'Failed to load image details';
    }
  } catch (err) {
    console.error('Error loading image details:', err);
    error.value = err.response?.data?.message || 'Failed to load image details';
  } finally {
    loading.value = false;
  }
};

const formatFileSize = (bytes) => {
  if (!bytes) return 'N/A';
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
};

const downloadImage = () => {
  if (imageData.value) {
    const link = document.createElement('a');
    link.href = `${API_BASE_URL}/api/v2/images/${imageData.value.id}/file`;
    link.download = imageData.value.original_filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

const editImage = () => {
  if (imageData.value) {
    window.open(`${API_BASE_URL}/api/v2/images/${imageData.value.id}/file`, '_blank');
  }
};

const openLightbox = () => {
  visibleRef.value = true;
};

const reprocessImage = async () => {
  try {
    await apiService.images.reprocess(route.params.id);
    alert('Image queued for reprocessing');
    await loadImageDetails();
  } catch (err) {
    console.error('Error reprocessing image:', err);
    alert('Failed to reprocess image');
  }
};

const getStatusVariant = (status) => {
  switch (status) {
    case 'completed': return 'default';
    case 'processing': return 'secondary';
    case 'failed': return 'destructive';
    case 'pending': return 'outline';
    default: return 'outline';
  }
};
</script>

<template>
  <div class="w-full max-w-[1400px] mx-auto p-6 space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <Button @click="router.back()" variant="ghost" class="gap-2">
        <ArrowLeft class="h-4 w-4" />
        Back
      </Button>

      <div v-if="imageData" class="flex gap-2">
        <Button @click="downloadImage" variant="default" size="sm" class="gap-2">
          <Download class="h-4 w-4" />
          Download
        </Button>
        <Button @click="editImage" variant="secondary" size="sm" class="gap-2">
          <Edit2 class="h-4 w-4" />
          Edit
        </Button>
        <Button @click="reprocessImage" variant="outline" size="sm" class="gap-2">
          <RefreshCw class="h-4 w-4" />
          Reprocess
        </Button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center min-h-[400px]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col justify-center items-center min-h-[400px]">
      <p class="text-destructive text-lg mb-4">{{ error }}</p>
      <Button @click="router.back()" variant="outline">Go Back</Button>
    </div>

    <!-- Image Details -->
    <div v-else-if="imageData" class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Image Preview (Left Side - 2 columns) -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Main Image -->
        <Card>
          <CardContent class="p-6">
            <div class="relative group">
              <img
                :src="`${API_BASE_URL}/api/v2/images/${imageData.id}/file`"
                :alt="imageData.original_filename"
                class="w-full h-auto rounded-lg cursor-pointer"
                @click="openLightbox"
              />
              <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all rounded-lg flex items-center justify-center">
                <Button
                  @click="openLightbox"
                  variant="secondary"
                  class="opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  View Full Size
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Extracted Text -->
        <Card v-if="imageData.extracted_text">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <FileText class="h-5 w-5" />
              Extracted Text (OCR)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p class="text-sm whitespace-pre-wrap bg-muted p-4 rounded-lg">{{ imageData.extracted_text }}</p>
          </CardContent>
        </Card>

        <!-- EXIF Data -->
        <Card v-if="imageData.exif_data && Object.keys(imageData.exif_data).length > 0">
          <CardHeader>
            <CardTitle class="flex items-center gap-2">
              <ImageIcon class="h-5 w-5" />
              EXIF Data
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div class="grid grid-cols-2 gap-3">
              <div v-for="(value, key) in imageData.exif_data" :key="key" class="text-sm">
                <span class="font-semibold text-muted-foreground">{{ key }}:</span>
                <span class="ml-2">{{ value }}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Details Sidebar (Right Side - 1 column) -->
      <div class="space-y-6">
        <!-- Basic Info -->
        <Card>
          <CardHeader>
            <CardTitle>Image Information</CardTitle>
          </CardHeader>
          <CardContent class="space-y-4">
            <!-- Filename -->
            <div>
              <label class="text-xs font-semibold text-muted-foreground uppercase">Filename</label>
              <p class="text-sm mt-1 break-all font-medium">{{ imageData.original_filename }}</p>
            </div>

            <Separator />

            <!-- Status -->
            <div>
              <label class="text-xs font-semibold text-muted-foreground uppercase">Status</label>
              <div class="mt-1">
                <Badge :variant="getStatusVariant(imageData.status)">{{ imageData.status }}</Badge>
              </div>
            </div>

            <Separator />

            <!-- File Size -->
            <div class="flex items-center gap-2">
              <HardDrive class="h-4 w-4 text-muted-foreground" />
              <div class="flex-1">
                <label class="text-xs font-semibold text-muted-foreground uppercase">File Size</label>
                <p class="text-sm font-medium">{{ formatFileSize(imageData.file_size) }}</p>
              </div>
            </div>

            <!-- Dimensions -->
            <div v-if="imageData.width && imageData.height" class="flex items-center gap-2">
              <ImageIcon class="h-4 w-4 text-muted-foreground" />
              <div class="flex-1">
                <label class="text-xs font-semibold text-muted-foreground uppercase">Dimensions</label>
                <p class="text-sm font-medium">{{ imageData.width }} × {{ imageData.height }}px</p>
              </div>
            </div>

            <!-- MIME Type -->
            <div>
              <label class="text-xs font-semibold text-muted-foreground uppercase">Format</label>
              <p class="text-sm font-medium">{{ imageData.mime_type }}</p>
            </div>

            <Separator />

            <!-- Upload Date -->
            <div class="flex items-center gap-2">
              <Calendar class="h-4 w-4 text-muted-foreground" />
              <div class="flex-1">
                <label class="text-xs font-semibold text-muted-foreground uppercase">Uploaded</label>
                <p class="text-sm font-medium">{{ formatDate(imageData.created_at) }}</p>
              </div>
            </div>

            <!-- Image Date (from EXIF) -->
            <div v-if="imageData.image_date" class="flex items-center gap-2">
              <Calendar class="h-4 w-4 text-muted-foreground" />
              <div class="flex-1">
                <label class="text-xs font-semibold text-muted-foreground uppercase">Captured</label>
                <p class="text-sm font-medium">{{ formatDate(imageData.image_date) }}</p>
              </div>
            </div>

            <!-- Location -->
            <div v-if="imageData.location" class="flex items-center gap-2">
              <MapPin class="h-4 w-4 text-muted-foreground" />
              <div class="flex-1">
                <label class="text-xs font-semibold text-muted-foreground uppercase">Location</label>
                <p class="text-sm font-medium">{{ imageData.location }}</p>
              </div>
            </div>

            <Separator />

            <!-- Image ID -->
            <div>
              <label class="text-xs font-semibold text-muted-foreground uppercase">Image ID</label>
              <p class="text-sm font-mono mt-1">{{ imageData.id }}</p>
            </div>
          </CardContent>
        </Card>

        <!-- Processing Metrics -->
        <Card v-if="imageData.metrics && Object.keys(imageData.metrics).length > 0">
          <CardHeader>
            <CardTitle>Processing Metrics</CardTitle>
          </CardHeader>
          <CardContent class="space-y-2">
            <div v-for="(value, key) in imageData.metrics" :key="key" class="flex justify-between text-sm">
              <span class="text-muted-foreground">{{ key }}:</span>
              <span class="font-medium">{{ value }}</span>
            </div>
          </CardContent>
        </Card>

        <!-- Metadata -->
        <Card v-if="imageData.metadata && Object.keys(imageData.metadata).length > 0">
          <CardHeader>
            <CardTitle>Additional Metadata</CardTitle>
          </CardHeader>
          <CardContent class="space-y-2">
            <div v-for="(value, key) in imageData.metadata" :key="key" class="flex justify-between text-sm">
              <span class="text-muted-foreground">{{ key }}:</span>
              <span class="font-medium">{{ value }}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Lightbox -->
    <VueEasyLightbox
      v-if="imageData"
      :visible="visibleRef"
      :imgs="[`${API_BASE_URL}/api/v2/images/${imageData.id}/file`]"
      :index="0"
      @hide="visibleRef = false"
    />
  </div>
</template>
