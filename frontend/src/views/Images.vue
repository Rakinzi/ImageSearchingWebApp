<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { Search, Grid3x3, Grid2x2, List, RefreshCcw, Upload, Download, Edit2, Info, X } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import VueEasyLightbox from 'vue-easy-lightbox';
import { useImagesStore } from '../stores/imagesStore';
import { API_BASE_URL } from '../services/api';
import { useRouter } from 'vue-router';
import { useDebounceFn } from '@vueuse/core';

const router = useRouter();
const imagesStore = useImagesStore();

const searchQuery = ref('');
const searchType = ref('semantic'); // 'semantic', 'text', 'metadata'
const loading = ref(false);
const displayedImages = ref([]);
const viewMode = ref('grid'); // 'grid', 'masonry', 'list'
const visibleRef = ref(false);
const indexRef = ref(0);
const imagesRef = computed(() => displayedImages.value.map(img => img.fullUrl));

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

// Advanced natural language date parsing
const parseNaturalLanguageDate = (query) => {
  const months = ['january', 'february', 'march', 'april', 'may', 'june',
                  'july', 'august', 'september', 'october', 'november', 'december'];

  const currentYear = new Date().getFullYear();
  const lowerQuery = query.toLowerCase().trim();

  // Extract keywords and date info
  let keywords = [];
  let dateFilter = null;

  // Pattern 1: "this year", "last year", "2024", "2023"
  const thisYearMatch = lowerQuery.match(/this\s+year/);
  const lastYearMatch = lowerQuery.match(/last\s+year/);
  const specificYearMatch = lowerQuery.match(/\b(20\d{2})\b/);

  if (thisYearMatch) {
    dateFilter = { year: currentYear };
    keywords = lowerQuery.replace(/this\s+year/g, '').trim().split(/\s+/).filter(k => k);
  } else if (lastYearMatch) {
    dateFilter = { year: currentYear - 1 };
    keywords = lowerQuery.replace(/last\s+year/g, '').trim().split(/\s+/).filter(k => k);
  } else if (specificYearMatch) {
    const year = parseInt(specificYearMatch[1]);
    dateFilter = { year };
    keywords = lowerQuery.replace(/\b20\d{2}\b/g, '').trim().split(/\s+/).filter(k => k);
  }

  // Pattern 2: "this month", "last month"
  const thisMonthMatch = lowerQuery.match(/this\s+month/);
  const lastMonthMatch = lowerQuery.match(/last\s+month/);

  if (thisMonthMatch) {
    const now = new Date();
    dateFilter = { year: now.getFullYear(), month: now.getMonth() + 1 };
    keywords = lowerQuery.replace(/this\s+month/g, '').trim().split(/\s+/).filter(k => k);
  } else if (lastMonthMatch) {
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);
    dateFilter = { year: lastMonth.getFullYear(), month: lastMonth.getMonth() + 1 };
    keywords = lowerQuery.replace(/last\s+month/g, '').trim().split(/\s+/).filter(k => k);
  }

  // Pattern 3: "DD Month" or "Month DD" with optional year
  const dayMonthPattern = /(\d{1,2})\s+(\w+)(?:\s+(\d{4}))?/;
  const monthDayPattern = /(\w+)\s+(\d{1,2})(?:\s+(\d{4}))?/;

  let dateMatch = lowerQuery.match(dayMonthPattern) || lowerQuery.match(monthDayPattern);

  if (dateMatch && !dateFilter) {
    const [fullMatch, first, second, year] = dateMatch;
    let day, monthName;

    if (isNaN(first)) {
      monthName = first;
      day = parseInt(second);
    } else {
      day = parseInt(first);
      monthName = second;
    }

    const monthIndex = months.findIndex(m => m.startsWith(monthName.toLowerCase()));

    if (monthIndex !== -1 && day >= 1 && day <= 31) {
      dateFilter = {
        day,
        month: monthIndex + 1,
        year: year ? parseInt(year) : null
      };
      keywords = lowerQuery.replace(fullMatch, '').trim().split(/\s+/).filter(k => k);
    }
  }

  // Pattern 4: Month names with "this" or "last"
  const monthWithModifier = lowerQuery.match(/(this|last)\s+(\w+)/);
  if (monthWithModifier && !dateFilter) {
    const [fullMatch, modifier, monthName] = monthWithModifier;
    const monthIndex = months.findIndex(m => m.startsWith(monthName.toLowerCase()));

    if (monthIndex !== -1) {
      const now = new Date();
      const targetMonth = monthIndex + 1;
      let targetYear = now.getFullYear();

      if (modifier === 'last') {
        // If it's January and we say "last december", it means previous year
        if (targetMonth > now.getMonth() + 1) {
          targetYear--;
        } else if (targetMonth === now.getMonth() + 1) {
          targetYear--;
        }
      }

      dateFilter = { month: targetMonth, year: targetYear };
      keywords = lowerQuery.replace(fullMatch, '').trim().split(/\s+/).filter(k => k);
    }
  }

  // Pattern 5: Special dates (christmas, halloween, new year, etc.)
  const specialDates = {
    'christmas': { day: 25, month: 12 },
    'halloween': { day: 31, month: 10 },
    'new year': { day: 1, month: 1 },
    'valentine': { day: 14, month: 2 },
    'easter': null, // Easter varies, skip for now
    'thanksgiving': null // Thanksgiving varies, skip for now
  };

  for (const [holiday, date] of Object.entries(specialDates)) {
    if (date && lowerQuery.includes(holiday)) {
      // Extract year modifiers
      const holidayYear = lowerQuery.match(/this\s+year/) ? currentYear :
                         lowerQuery.match(/last\s+year/) ? currentYear - 1 :
                         lowerQuery.match(/\b(20\d{2})\b/) ? parseInt(lowerQuery.match(/\b(20\d{2})\b/)[1]) :
                         null;

      dateFilter = {
        day: date.day,
        month: date.month,
        year: holidayYear
      };
      keywords = [holiday];
      break;
    }
  }

  return {
    keywords: keywords.length > 0 ? keywords.join(' ') : null,
    dateFilter
  };
};

const fetchImages = async (query) => {
  loading.value = true;
  try {
    // Parse natural language query
    const { keywords, dateFilter } = parseNaturalLanguageDate(query);

    console.log('Parsed query:', { keywords, dateFilter, originalQuery: query });

    if (keywords || dateFilter) {
      // Hybrid search: semantic + date filtering
      let results = [];

      if (keywords) {
        // Perform search with keywords using selected search type
        results = await imagesStore.searchImages(keywords, searchType.value, {
          similarityThreshold: 0.3,
          limit: 100 // Get more results for date filtering
        });
        console.log(`Search completed: ${results.length} results found for "${keywords}" (${searchType.value})`);
      } else {
        // No keywords, just date filter - get all images
        await imagesStore.loadImages(1, true);
        results = imagesStore.images;
      }

      // Apply date filter if specified
      if (dateFilter) {
        results = results.filter(image => {
          if (!image.created_at) return false;
          const date = new Date(image.created_at);

          // Match year if specified
          if (dateFilter.year && date.getFullYear() !== dateFilter.year) {
            return false;
          }

          // Match month if specified
          if (dateFilter.month && date.getMonth() + 1 !== dateFilter.month) {
            return false;
          }

          // Match day if specified
          if (dateFilter.day && date.getDate() !== dateFilter.day) {
            return false;
          }

          return true;
        });
      }

      displayedImages.value = results.map(image => ({
        id: image.id,
        thumbnailUrl: `${API_BASE_URL}/api/v2/images/${image.id}/thumbnail`,
        fullUrl: `${API_BASE_URL}/api/v2/images/${image.id}/file`,
        filename: image.filename || 'Untitled',
        created_at: image.created_at,
        status: image.status,
        similarity: image.similarity_score
      }));
    } else {
      // Fallback to regular search with selected type
      const results = await imagesStore.searchImages(query, searchType.value, {
        similarityThreshold: 0.3,
        limit: 50
      });
      console.log(`Search completed: ${results.length} results found for "${query}" (${searchType.value})`);
      displayedImages.value = results.map(image => ({
        id: image.id,
        thumbnailUrl: `${API_BASE_URL}/api/v2/images/${image.id}/thumbnail`,
        fullUrl: `${API_BASE_URL}/api/v2/images/${image.id}/file`,
        filename: image.filename || 'Untitled',
        created_at: image.created_at,
        status: image.status,
        similarity: image.similarity_score
      }));
    }
  } catch (error) {
    console.error("Error searching images:", error);
    displayedImages.value = [];
  } finally {
    loading.value = false;
  }
};

// Debounced search function
const debouncedSearch = useDebounceFn(() => {
  if (searchQuery.value.trim() !== '') {
    fetchImages(searchQuery.value);
  } else {
    updateDisplayedImages();
  }
}, 500);

// Watch for search query changes
watch(searchQuery, () => {
  debouncedSearch();
});

const handleSearch = () => {
  if (searchQuery.value.trim() !== '') {
    fetchImages(searchQuery.value);
  } else {
    updateDisplayedImages();
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  updateDisplayedImages();
};

const handleKeyPress = (event) => {
  if (event.key === 'Enter') {
    handleSearch();
  }
};

const gridClass = computed(() => {
  switch (viewMode.value) {
    case 'grid':
      return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4';
    case 'masonry':
      return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3';
    case 'list':
      return 'flex flex-col gap-4';
    default:
      return 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4';
  }
});

const imageHeight = computed(() => {
  return viewMode.value === 'list' ? 'h-28' : 'h-72';
});

const openLightbox = (index) => {
  indexRef.value = index;
  visibleRef.value = true;
};

const viewImageDetail = (imageId) => {
  router.push(`/images/${imageId}`);
};

const closeLightbox = () => {
  visibleRef.value = false;
};

const downloadImage = () => {
  const currentImage = displayedImages.value[indexRef.value];
  if (currentImage) {
    const link = document.createElement('a');
    link.href = currentImage.fullUrl;
    link.download = currentImage.filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
};

const editImage = () => {
  const currentImage = displayedImages.value[indexRef.value];
  if (currentImage) {
    // Open image in new tab for editing (or implement your own editor)
    window.open(currentImage.fullUrl, '_blank');
  }
};

const showImageInfo = () => {
  const currentImage = displayedImages.value[indexRef.value];
  if (currentImage) {
    // Navigate to detail page
    router.push(`/images/${currentImage.id}`);
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
</script>

<template>
  <div class="w-full max-w-[1600px] mx-auto p-6">
    <!-- Header Section -->
    <div class="flex justify-between items-start mb-8 pb-6 border-b">
      <div class="flex-1">
        <div class="flex items-center mb-2">
          <h1 class="text-4xl font-bold tracking-tight">My Gallery</h1>
          <Badge variant="secondary" class="ml-3">{{ displayedImages.length }}</Badge>
        </div>
        <p class="text-muted-foreground text-base">
          Browse, search, and manage your image collection
        </p>
      </div>

      <Button @click="router.push('/upload')" size="lg" class="ml-6">
        <Upload class="mr-2 h-5 w-5" />
        Upload Images
      </Button>
    </div>

    <!-- Search and Controls Bar -->
    <div class="flex gap-4 mb-8 items-center flex-wrap">
      <div class="relative flex-1 max-w-xl">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
        <Input
          v-model="searchQuery"
          :placeholder="searchType === 'semantic'
            ? 'Describe what you\'re looking for... (e.g., \'person in red shirt\', \'graduation this year\')'
            : searchType === 'text'
            ? 'Search text in images (OCR)...'
            : 'Search metadata and filenames...'"
          class="pl-10 pr-10 h-11"
          @keyup="handleKeyPress"
        />
        <button
          v-if="searchQuery"
          @click="clearSearch"
          class="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      <div class="flex gap-3 items-center">
        <!-- Search Type Selector -->
        <div class="flex rounded-md border bg-background">
          <Button
            :variant="searchType === 'semantic' ? 'default' : 'ghost'"
            @click="searchType = 'semantic'"
            size="sm"
            class="rounded-r-none"
            title="AI-powered descriptive search"
          >
            <Search class="h-4 w-4 mr-1" />
            Semantic
          </Button>
          <Button
            :variant="searchType === 'text' ? 'default' : 'ghost'"
            @click="searchType = 'text'"
            size="sm"
            class="rounded-none border-x"
            title="Search extracted text (OCR)"
          >
            Text
          </Button>
          <Button
            :variant="searchType === 'metadata' ? 'default' : 'ghost'"
            @click="searchType = 'metadata'"
            size="sm"
            class="rounded-l-none"
            title="Search filenames and metadata"
          >
            Metadata
          </Button>
        </div>

        <Button
          @click="handleSearch"
          :disabled="!searchQuery.trim()"
          variant="secondary"
          size="lg"
        >
          Search
        </Button>

        <Button
          @click="loadImages"
          :disabled="loading"
          variant="outline"
          size="lg"
          class="w-11 p-0"
        >
          <RefreshCcw class="h-5 w-5" :class="{ 'animate-spin': loading }" />
        </Button>

        <!-- View Mode Toggles -->
        <div class="flex rounded-md border">
          <Button
            :variant="viewMode === 'grid' ? 'default' : 'ghost'"
            @click="viewMode = 'grid'"
            size="lg"
            class="rounded-r-none border-r"
          >
            <Grid3x3 class="h-5 w-5" />
          </Button>
          <Button
            :variant="viewMode === 'masonry' ? 'default' : 'ghost'"
            @click="viewMode = 'masonry'"
            size="lg"
            class="rounded-none border-r"
          >
            <Grid2x2 class="h-5 w-5" />
          </Button>
          <Button
            :variant="viewMode === 'list' ? 'default' : 'ghost'"
            @click="viewMode = 'list'"
            size="lg"
            class="rounded-l-none"
          >
            <List class="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && displayedImages.length === 0" class="flex flex-col justify-center items-center min-h-[400px]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      <p class="mt-4 text-muted-foreground">Loading images...</p>
    </div>

    <!-- Empty State -->
    <div v-else-if="displayedImages.length === 0" class="flex flex-col justify-center items-center min-h-[400px]">
      <Upload class="h-20 w-20 text-muted-foreground/30 mb-4" />
      <h3 class="text-xl font-semibold mb-2">No images in your gallery yet</h3>
      <p class="text-muted-foreground mb-6">Start by uploading some images</p>
      <div class="flex gap-3">
        <Button @click="loadImages" :disabled="loading" variant="outline">
          <RefreshCcw class="mr-2 h-4 w-4" />
          Refresh
        </Button>
        <Button @click="router.push('/upload')">
          <Upload class="mr-2 h-4 w-4" />
          Upload Images
        </Button>
      </div>
    </div>

    <!-- Images Grid/Masonry/List -->
    <div v-else :class="gridClass">
      <!-- Grid/Masonry View -->
      <template v-if="viewMode !== 'list'">
        <div
          v-for="(image, index) in displayedImages"
          :key="image.id"
          class="group relative overflow-hidden rounded-lg cursor-pointer transition-all hover:-translate-y-2 hover:shadow-xl bg-muted"
          @click="openLightbox(index)"
        >
          <img
            :src="image.thumbnailUrl"
            :alt="image.filename"
            :class="imageHeight"
            class="w-full object-cover"
            loading="lazy"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
            <div class="absolute bottom-0 left-0 right-0 p-4">
              <p class="text-white text-sm font-medium truncate">{{ image.filename }}</p>
              <p v-if="image.similarity" class="text-white/80 text-xs mt-1">
                Match: {{ Math.round(image.similarity * 100) }}%
              </p>
            </div>
          </div>
        </div>
      </template>

      <!-- List View -->
      <template v-else>
        <Card
          v-for="(image, index) in displayedImages"
          :key="image.id"
          class="transition-all hover:translate-x-2 hover:shadow-md cursor-pointer"
          @click="openLightbox(index)"
        >
          <CardContent class="p-4">
            <div class="flex gap-5 items-center">
              <img
                :src="image.thumbnailUrl"
                :alt="image.filename"
                class="w-28 h-28 rounded-lg object-cover flex-shrink-0"
                loading="lazy"
              />
              <div class="flex-1 flex flex-col">
                <p class="font-semibold text-base">{{ image.filename }}</p>
                <p class="text-muted-foreground text-sm mt-2">
                  Uploaded: {{ new Date(image.created_at).toLocaleDateString() }}
                </p>
                <div class="mt-3">
                  <Badge :variant="image.status === 'completed' ? 'default' : 'secondary'">
                    {{ image.status }}
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </template>
    </div>

    <!-- Lightbox -->
    <VueEasyLightbox
      :visible="visibleRef"
      :imgs="imagesRef"
      :index="indexRef"
      @hide="closeLightbox"
      :loop="true"
      :move-disabled="false"
      :zoom-disabled="false"
      :rotate-disabled="false"
    >
      <template v-slot:toolbar="{ toolbarMethods }">
        <div class="flex gap-2 flex-wrap justify-center">
          <!-- Download, Edit & Info -->
          <button
            @click="downloadImage"
            class="flex items-center gap-2 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            title="Download Image"
          >
            <Download class="h-4 w-4" />
            <span class="text-sm">Download</span>
          </button>
          <button
            @click="editImage"
            class="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            title="Edit Image"
          >
            <Edit2 class="h-4 w-4" />
            <span class="text-sm">Edit</span>
          </button>
          <button
            @click="showImageInfo"
            class="flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            title="Image Details"
          >
            <Info class="h-4 w-4" />
            <span class="text-sm">Info</span>
          </button>

          <!-- Zoom Controls -->
          <button
            @click="toolbarMethods.zoomIn"
            class="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors text-lg font-bold"
            title="Zoom In"
          >
            +
          </button>
          <button
            @click="toolbarMethods.zoomOut"
            class="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors text-lg font-bold"
            title="Zoom Out"
          >
            −
          </button>

          <!-- Rotate Controls -->
          <button
            @click="toolbarMethods.rotateLeft"
            class="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors text-lg"
            title="Rotate Left"
          >
            ↺
          </button>
          <button
            @click="toolbarMethods.rotateRight"
            class="px-3 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors text-lg"
            title="Rotate Right"
          >
            ↻
          </button>
        </div>
      </template>
    </VueEasyLightbox>
  </div>
</template>
