<template>
  <div>
    <!-- Page Header -->
    <div style="margin-bottom: 24px">
      <n-text tag="h1" :depth="1" style="font-size: 28px; font-weight: 600; margin: 0;">
        People
      </n-text>
      <n-text :depth="3" style="margin-top: 8px; display: block;">
        Detected faces from your uploaded images
      </n-text>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" style="display: flex; justify-content: center; align-items: center; min-height: 400px;">
      <n-spin size="large" />
    </div>

    <!-- Empty State -->
    <div v-else-if="!faceData || !faceData.face_images || faceData.face_images.length === 0">
      <n-empty description="No faces detected yet">
        <template #extra>
          <n-button @click="ReloadFaceData" :loading="isLoading">
            Refresh
          </n-button>
        </template>
      </n-empty>
    </div>

    <!-- Face Grid -->
    <div v-else>
      <n-grid :x-gap="16" :y-gap="16" :cols="'1 600:2 900:3 1200:4 1600:5'" responsive="screen">
        <n-grid-item v-for="faceImage in faceData.face_images" :key="extractIdFromImage(faceImage)">
          <n-card
            hoverable
            @click="goToRelatedImages(extractIdFromImage(faceImage))"
            style="cursor: pointer; overflow: hidden;"
          >
            <n-image
              :src="faceImage"
              object-fit="cover"
              style="width: 100%; height: 200px; border-radius: 6px;"
              preview-disabled
              lazy
              :fallback-src="'/placeholder-face.png'"
            />
            <template #footer>
              <n-text :depth="3" style="font-size: 12px;">
                Face ID: {{ extractIdFromImage(faceImage) }}
              </n-text>
            </template>
          </n-card>
        </n-grid-item>
      </n-grid>

      <!-- Stats -->
      <div style="margin-top: 24px; text-align: center;">
        <n-text :depth="3">
          Found {{ faceData.face_images.length }} faces
        </n-text>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  NText,
  NSpin,
  NEmpty,
  NGrid,
  NGridItem,
  NCard,
  NImage,
  NButton,
  useMessage
} from 'naive-ui';
import { useFaceStore } from '../stores/FaceStore';

const router = useRouter();
const message = useMessage();
const faceStore = useFaceStore();

const { isLoading, faceData, loadFaceData, error } = faceStore;

const ReloadFaceData = async () => {
  try {
    await loadFaceData();
    if (faceStore.error) {
      message.error(faceStore.error);
    }
  } catch (err) {
    message.error('Failed to load face data');
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
