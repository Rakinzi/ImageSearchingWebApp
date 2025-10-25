<template>
  <div>
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold tracking-tight">People</h1>
      <p class="text-muted-foreground mt-1">Detected faces from your uploaded images</p>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center min-h-[400px]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!faceData || !faceData.face_images || faceData.face_images.length === 0">
      <div class="flex flex-col items-center justify-center min-h-[400px]">
        <Users class="h-20 w-20 text-muted-foreground/30 mb-4" />
        <h3 class="text-xl font-semibold mb-2">No faces detected yet</h3>
        <p class="text-muted-foreground mb-6">Upload some images to detect faces</p>
        <Button @click="ReloadFaceData" :disabled="isLoading">
          <RefreshCcw class="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>
    </div>

    <!-- Face Grid -->
    <div v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <Card
          v-for="faceImage in faceData.face_images"
          :key="extractIdFromImage(faceImage)"
          class="cursor-pointer hover:shadow-lg transition-shadow overflow-hidden"
          @click="goToRelatedImages(extractIdFromImage(faceImage))"
        >
          <CardContent class="p-0">
            <img
              :src="faceImage"
              alt="Face"
              class="w-full h-48 object-cover"
              loading="lazy"
            />
            <div class="p-3">
              <p class="text-xs text-muted-foreground">
                Face ID: {{ extractIdFromImage(faceImage) }}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Stats -->
      <div class="mt-6 text-center">
        <p class="text-muted-foreground">
          Found {{ faceData.face_images.length }} faces
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { Users, RefreshCcw } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { useFaceStore } from '../stores/FaceStore';

const router = useRouter();
const faceStore = useFaceStore();

const { isLoading, faceData, loadFaceData, error } = faceStore;

const ReloadFaceData = async () => {
  try {
    await loadFaceData();
    if (faceStore.error) {
      alert(faceStore.error);
    }
  } catch (err) {
    alert('Failed to load face data');
  }
};

const extractIdFromImage = (imageFilename) => {
  const match = imageFilename.match(/faces\\(.*?)(?:\.jpg|\.jpeg|\.png)$/);
  return match ? match[1] : null;
};

const goToRelatedImages = (faceId) => {
  console.log(faceId);
  router.push(`/faces/${faceId}`);
};

// Fetch face data using Pinia when the component mounts
onMounted(async () => {
  await ReloadFaceData();
});
</script>
