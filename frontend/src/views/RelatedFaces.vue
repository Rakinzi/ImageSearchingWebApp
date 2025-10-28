<template>
  <div class="p-6">
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold tracking-tight">Images with this Face</h1>
      <p v-if="faceInfo" class="text-muted-foreground mt-1">
        {{ faceInfo.person_name || 'Unknown Person' }} - {{ relatedImages.length }} images found
      </p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center min-h-[400px]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex flex-col items-center justify-center min-h-[400px]">
      <p class="text-red-500 mb-4">{{ error }}</p>
      <Button @click="loadRelatedImages" variant="outline">
        Try Again
      </Button>
    </div>

    <!-- Images Grid -->
    <div v-else-if="relatedImages.length" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <Card
        v-for="(image, index) in relatedImages"
        :key="index"
        class="overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
        @click="viewImage(image)"
      >
        <CardContent class="p-0">
          <img
            :src="API_BASE_URL + image.thumbnail_url"
            :alt="image.filename"
            class="w-full h-64 object-cover"
            loading="lazy"
          />
          <div class="p-3">
            <p class="text-sm font-medium truncate">{{ image.filename }}</p>
            <p class="text-xs text-muted-foreground mt-1">
              {{ new Date(image.created_at).toLocaleDateString() }}
            </p>
            <Badge v-if="image.face_count > 1" variant="secondary" class="mt-2">
              {{ image.face_count }} faces
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>

    <!-- Empty State -->
    <div v-else class="flex flex-col items-center justify-center min-h-[400px]">
      <h3 class="text-xl font-semibold mb-2">No images found</h3>
      <p class="text-muted-foreground">This face doesn't appear in any images</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { apiService, API_BASE_URL } from '../services/api';

const route = useRoute();
const router = useRouter();
const faceId = route.params.faceId; // Get face ID from the route params
const relatedImages = ref([]); // To store related images
const faceInfo = ref(null);
const loading = ref(false);
const error = ref(null);

const loadRelatedImages = async () => {
  loading.value = true;
  error.value = null;

  try {
    const response = await apiService.faces.getImages(faceId);
    console.log('Face images response:', response.data);

    relatedImages.value = response.data.images || [];
    faceInfo.value = {
      face_id: response.data.face_id,
      person_name: response.data.person_name,
      face_cluster_id: response.data.face_cluster_id,
      total_similar_faces: response.data.total_similar_faces
    };
  } catch (err) {
    console.error('Error fetching related images:', err);
    error.value = 'Failed to load images. Please try again.';
  } finally {
    loading.value = false;
  }
};

const viewImage = (image) => {
  // Navigate to image detail page
  if (image.type === 'modern') {
    router.push(`/images/${image.id}`);
  } else {
    // Handle legacy images if needed
    console.log('Legacy image clicked:', image.id);
  }
};

// Fetch related images when the component mounts
onMounted(() => {
  loadRelatedImages();
});
</script>
  