<template>
  <div>
    <!-- Page Header -->
    <div class="mb-6">
      <h1 class="text-3xl font-bold tracking-tight">People</h1>
      <p class="text-muted-foreground mt-1">Detected faces from your uploaded images</p>
    </div>

    <div v-if="error" class="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
      {{ error }}
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="flex justify-center items-center min-h-[400px]">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!faceData || !faceData.faces || faceData.faces.length === 0">
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
          v-for="face in faceData.faces"
          :key="face.id"
          class="hover:shadow-lg transition-shadow overflow-hidden"
        >
          <CardContent class="p-0">
            <img
              :src="getFaceImageUrl(face.id)"
              alt="Face"
              class="w-full h-48 object-cover cursor-pointer transition-transform duration-150 hover:scale-[1.01]"
              loading="lazy"
              @click="goToRelatedImages(face.id)"
            />
            <div class="p-3 space-y-3">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold leading-tight">
                    {{ face.person_name || 'Unlabeled face' }}
                  </p>
                  <p class="text-xs text-muted-foreground">
                    Face ID: {{ face.id }}
                  </p>
                </div>
                <Badge
                  v-if="face.person_name"
                  variant="secondary"
                  class="text-[11px] uppercase tracking-wide"
                >
                  {{ face.manual_verification ? 'Manual' : 'Auto' }}
                </Badge>
              </div>

              <div class="space-y-2" @click.stop>
                <Input
                  v-model="labelInputs[face.id]"
                  placeholder="Add a name"
                  class="h-9"
                  @keyup.enter="saveLabel(face)"
                />
                <div class="flex items-center gap-2">
                  <Button
                    size="sm"
                    @click="saveLabel(face)"
                    :disabled="isFaceUpdating(face.id) || !canSaveLabel(face)"
                  >
                    <Loader2
                      v-if="isFaceUpdating(face.id)"
                      class="mr-2 h-4 w-4 animate-spin"
                    />
                    <span>Save label</span>
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    class="text-muted-foreground hover:text-foreground"
                    @click="resetLabel(face)"
                    :disabled="isFaceUpdating(face.id)"
                  >
                    Reset
                  </Button>
                </div>
                <p
                  v-if="statusMessages[face.id]"
                  class="text-xs"
                  :class="{
                    'text-red-500': statusMessages[face.id].type === 'error',
                    'text-emerald-600': statusMessages[face.id].type === 'success',
                    'text-muted-foreground': statusMessages[face.id].type === 'info'
                  }"
                >
                  {{ statusMessages[face.id].text }}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Stats -->
      <div class="mt-6 text-center">
        <p class="text-muted-foreground">
          Found {{ faceData.faces.length }} faces
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import { Users, RefreshCcw, Loader2 } from 'lucide-vue-next';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useFaceStore } from '../stores/FaceStore';
import { API_BASE_URL } from '../services/api';

const router = useRouter();
const faceStore = useFaceStore();

// Use storeToRefs to maintain reactivity when destructuring
const { isLoading, faceData, error, updatingFaces } = storeToRefs(faceStore);

const labelInputs = ref({});
const statusMessages = ref({});
const statusTimers = new Map();

const initializeLabelInputs = (faces = []) => {
  const next = faces.reduce((acc, face) => {
    acc[face.id] = face.person_name || '';
    return acc;
  }, {});
  labelInputs.value = next;
};

watch(
  faceData,
  (newValue) => {
    if (newValue?.faces) {
      initializeLabelInputs(newValue.faces);
    } else {
      labelInputs.value = {};
    }
  },
  { immediate: true }
);

const getFaceImageUrl = (faceId) => `${API_BASE_URL}/api/v2/faces/${faceId}/image`;

const isFaceUpdating = (faceId) => Boolean(updatingFaces.value?.[faceId]);

const canSaveLabel = (face) => {
  const currentValue = (labelInputs.value?.[face.id] ?? '').trim();
  const existing = (face.person_name ?? '').trim();
  return currentValue.length > 0 && currentValue !== existing;
};

const clearStatusMessage = (faceId) => {
  if (statusTimers.has(faceId)) {
    clearTimeout(statusTimers.get(faceId));
    statusTimers.delete(faceId);
  }
  if (statusMessages.value[faceId]) {
    const { [faceId]: _, ...rest } = statusMessages.value;
    statusMessages.value = rest;
  }
};

const setStatusMessage = (faceId, text, type = 'success') => {
  clearStatusMessage(faceId);
  statusMessages.value = {
    ...statusMessages.value,
    [faceId]: { text, type }
  };

  const timeoutId = window.setTimeout(() => {
    clearStatusMessage(faceId);
  }, 4000);

  statusTimers.set(faceId, timeoutId);
};

const saveLabel = async (face) => {
  const inputValue = labelInputs.value?.[face.id] ?? '';
  const trimmedName = inputValue.trim();

  if (!trimmedName) {
    setStatusMessage(face.id, 'Please enter a name before saving.', 'error');
    return;
  }

  if (!canSaveLabel(face)) {
    setStatusMessage(face.id, 'No changes to save.', 'info');
    return;
  }

  try {
    await faceStore.assignPersonToFace(face.id, trimmedName);
    labelInputs.value = {
      ...labelInputs.value,
      [face.id]: trimmedName
    };
    faceStore.clearError();
    setStatusMessage(face.id, 'Label saved successfully.', 'success');
  } catch (err) {
    console.error('Failed to assign label:', err);
    const message = err?.message || 'Failed to save label.';
    setStatusMessage(face.id, message, 'error');
  }
};

const resetLabel = (face) => {
  labelInputs.value = {
    ...labelInputs.value,
    [face.id]: face.person_name || ''
  };
  clearStatusMessage(face.id);
};

const ReloadFaceData = async () => {
  try {
    await faceStore.loadFaceData();
    console.log('Face data loaded:', faceData.value);
  } catch (err) {
    console.error('Failed to load face data:', err);
  }
};

const goToRelatedImages = (faceId) => {
  router.push(`/faces/${faceId}`);
};

onMounted(async () => {
  await ReloadFaceData();
});

onBeforeUnmount(() => {
  statusTimers.forEach((timeoutId) => clearTimeout(timeoutId));
  statusTimers.clear();
});
</script>
