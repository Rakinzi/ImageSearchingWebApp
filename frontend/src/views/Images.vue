<script setup>
import { ref, onMounted, computed } from 'vue';
import {
  NInput,
  NGrid,
  NGridItem,
  NImage,
  NImageGroup,
  NSpin,
  NEmpty,
  NIcon,
  NText,
  NButton,
  NCard,
  NSpace,
  NButtonGroup,
  NBadge,
  useMessage
} from 'naive-ui';
import {
  Search,
  GridOutline,
  AppsOutline,
  ListOutline,
  RefreshOutline,
  CloudUploadOutline
} from '@vicons/ionicons5';
import { useImagesStore } from '../stores/imagesStore';
import { API_BASE_URL } from '../services/api';

const imagesStore = useImagesStore();
const message = useMessage();

const searchQuery = ref('');
const loading = ref(false);
const displayedImages = ref([]);
const viewMode = ref('grid'); // 'grid', 'masonry', 'list'

onMounted(async () => {
  await loadImages();
});

const loadImages = async () => {
  loading.value = true;
  try {
    await imagesStore.loadImages();
    updateDisplayedImages();
  } catch (error) {
    console.error("Error loading images:", error);
    message.error("Failed to load images");
  } finally {
    loading.value = false;
  }
};

const updateDisplayedImages = () => {
  displayedImages.value = imagesStore.images.map(image => ({
    id: image.id,
    thumbnailUrl: `${API_BASE_URL}/api/v2/images/${image.id}/thumbnail`,
    fullUrl: `${API_BASE_URL}/api/v2/images/${image.id}/file`,
    filename: image.filename || 'Untitled',
    created_at: image.created_at,
    status: image.status
  }));
};

const fetchImages = async (query) => {
  loading.value = true;
  try {
    const results = await imagesStore.searchImages(query);
    displayedImages.value = results.map(image => ({
      id: image.id,
      thumbnailUrl: `${API_BASE_URL}/api/v2/images/${image.id}/thumbnail`,
      fullUrl: `${API_BASE_URL}/api/v2/images/${image.id}/file`,
      filename: image.filename || 'Untitled',
      created_at: image.created_at,
      status: image.status
    }));
    message.success(`Found ${results.length} images`);
  } catch (error) {
    console.error("Error searching images:", error);
    message.error("Failed to search images");
    displayedImages.value = [];
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  if (searchQuery.value.trim() !== '') {
    fetchImages(searchQuery.value);
  } else {
    updateDisplayedImages();
  }
};

const handleKeyPress = (event) => {
  if (event.key === 'Enter') {
    handleSearch();
  }
};

// Grid columns based on view mode
const gridCols = computed(() => {
  switch (viewMode.value) {
    case 'grid':
      return '1 500:2 800:3 1200:4';
    case 'masonry':
      return '1 500:2 800:3 1200:5';
    case 'list':
      return '1';
    default:
      return '1 500:2 800:3 1200:4';
  }
});

const imageHeight = computed(() => {
  switch (viewMode.value) {
    case 'grid':
      return '280px';
    case 'masonry':
      return 'auto';
    case 'list':
      return '120px';
    default:
      return '280px';
  }
});
</script>

<template>
  <div class="images-page">
    <!-- Header Section -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <n-text class="page-title">My Gallery</n-text>
          <n-badge
            :value="displayedImages.length"
            :max="999"
            type="info"
            style="margin-left: 12px;"
          />
        </div>
        <n-text class="page-subtitle">
          Browse, search, and manage your image collection
        </n-text>
      </div>

      <n-button
        type="primary"
        size="large"
        @click="$router.push('/upload')"
        class="upload-btn"
      >
        <template #icon>
          <n-icon>
            <CloudUploadOutline />
          </n-icon>
        </template>
        Upload Images
      </n-button>
    </div>

    <!-- Search and Controls Bar -->
    <div class="controls-bar">
      <n-input
        v-model:value="searchQuery"
        placeholder="Search your images..."
        size="large"
        clearable
        class="search-input"
        @keyup="handleKeyPress"
      >
        <template #prefix>
          <n-icon size="20">
            <Search />
          </n-icon>
        </template>
      </n-input>

      <n-space :size="12">
        <n-button
          size="large"
          @click="handleSearch"
          :disabled="!searchQuery.trim()"
          type="primary"
          secondary
        >
          Search
        </n-button>

        <n-button
          size="large"
          @click="loadImages"
          :loading="loading"
          circle
        >
          <template #icon>
            <n-icon>
              <RefreshOutline />
            </n-icon>
          </template>
        </n-button>

        <!-- View Mode Toggles -->
        <n-button-group size="large">
          <n-button
            :type="viewMode === 'grid' ? 'primary' : 'default'"
            @click="viewMode = 'grid'"
          >
            <template #icon>
              <n-icon>
                <GridOutline />
              </n-icon>
            </template>
          </n-button>
          <n-button
            :type="viewMode === 'masonry' ? 'primary' : 'default'"
            @click="viewMode = 'masonry'"
          >
            <template #icon>
              <n-icon>
                <AppsOutline />
              </n-icon>
            </template>
          </n-button>
          <n-button
            :type="viewMode === 'list' ? 'primary' : 'default'"
            @click="viewMode = 'list'"
          >
            <template #icon>
              <n-icon>
                <ListOutline />
              </n-icon>
            </template>
          </n-button>
        </n-button-group>
      </n-space>
    </div>

    <!-- Loading State -->
    <div v-if="imagesStore.loading || loading" class="loading-container">
      <n-spin size="large" />
      <n-text style="margin-top: 16px;">Loading images...</n-text>
    </div>

    <!-- Empty State -->
    <div v-else-if="displayedImages.length === 0" class="empty-container">
      <n-empty
        description="No images in your gallery yet"
        size="large"
      >
        <template #icon>
          <n-icon size="80" :depth="3">
            <CloudUploadOutline />
          </n-icon>
        </template>
        <template #extra>
          <n-space>
            <n-button @click="loadImages" :loading="loading" size="large">
              <template #icon>
                <n-icon>
                  <RefreshOutline />
                </n-icon>
              </template>
              Refresh
            </n-button>
            <n-button type="primary" @click="$router.push('/upload')" size="large">
              <template #icon>
                <n-icon>
                  <CloudUploadOutline />
                </n-icon>
              </template>
              Upload Images
            </n-button>
          </n-space>
        </template>
      </n-empty>
    </div>

    <!-- Images Grid/Masonry/List -->
    <div v-else class="images-container">
      <n-image-group>
        <!-- Grid/Masonry View -->
        <n-grid
          v-if="viewMode !== 'list'"
          :x-gap="16"
          :y-gap="16"
          :cols="gridCols"
          responsive="screen"
        >
          <n-grid-item v-for="image in displayedImages" :key="image.id">
            <div class="image-wrapper">
              <n-image
                :src="image.thumbnailUrl"
                :preview-src="image.fullUrl"
                object-fit="cover"
                :style="`width: 100%; height: ${imageHeight}; border-radius: 12px;`"
                lazy
                show-toolbar-tooltip
                class="gallery-image"
              />
              <div class="image-overlay">
                <n-text class="image-filename">{{ image.filename }}</n-text>
              </div>
            </div>
          </n-grid-item>
        </n-grid>

        <!-- List View -->
        <div v-else class="list-view">
          <n-card
            v-for="image in displayedImages"
            :key="image.id"
            :bordered="false"
            class="list-item"
          >
            <div class="list-item-content">
              <n-image
                :src="image.thumbnailUrl"
                :preview-src="image.fullUrl"
                object-fit="cover"
                style="width: 120px; height: 120px; border-radius: 8px; flex-shrink: 0;"
                lazy
                show-toolbar-tooltip
                class="list-image"
              />
              <div class="list-item-info">
                <n-text strong style="font-size: 16px;">{{ image.filename }}</n-text>
                <n-text :depth="3" style="margin-top: 8px;">
                  Uploaded: {{ new Date(image.created_at).toLocaleDateString() }}
                </n-text>
                <n-space style="margin-top: 12px;">
                  <n-badge
                    :value="image.status"
                    :type="image.status === 'completed' ? 'success' : 'warning'"
                  />
                </n-space>
              </div>
            </div>
          </n-card>
        </div>
      </n-image-group>
    </div>
  </div>
</template>

<style scoped>
.images-page {
  width: 100%;
  max-width: 1600px;
  margin: 0 auto;
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.header-content {
  flex: 1;
}

.title-section {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 16px;
  opacity: 0.65;
}

.upload-btn {
  flex-shrink: 0;
  margin-left: 24px;
}

.controls-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  align-items: center;
}

.search-input {
  flex: 1;
  max-width: 600px;
}

.loading-container,
.empty-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.images-container {
  margin-top: 0;
}

.image-wrapper {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #f5f5f5;
}

.image-wrapper:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
}

.image-wrapper:hover .image-overlay {
  opacity: 1;
}

.gallery-image {
  display: block;
  width: 100%;
}

.image-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7) 0%, transparent 100%);
  padding: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.image-filename {
  color: white;
  font-size: 14px;
  font-weight: 500;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.list-item {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.list-item:hover {
  transform: translateX(8px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.list-item-content {
  display: flex;
  gap: 20px;
  align-items: center;
}

.list-image {
  flex-shrink: 0;
}

.list-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .upload-btn {
    margin-left: 0;
    width: 100%;
  }

  .controls-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    max-width: none;
  }

  .page-title {
    font-size: 24px;
  }
}
</style>
