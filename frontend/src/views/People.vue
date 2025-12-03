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
    <div v-else-if="!clusters || !clusters.clusters || clusters.clusters.length === 0">
      <div class="flex flex-col items-center justify-center min-h-[400px]">
        <Users class="h-20 w-20 text-muted-foreground/30 mb-4" />
        <h3 class="text-xl font-semibold mb-2">No face groups yet</h3>
        <p class="text-muted-foreground mb-6">
          {{ faceData?.faces?.length > 0 ? 'Click "Group Similar Faces" to automatically group similar faces together' : 'Upload some images with faces first' }}
        </p>
        <div class="flex gap-3">
          <Button @click="handleClusterFaces" :disabled="isLoading || isClustering || !faceData?.faces?.length">
            <Loader2 v-if="isClustering" class="mr-2 h-4 w-4 animate-spin" />
            <span>{{ isClustering ? 'Grouping Faces...' : 'Group Similar Faces' }}</span>
          </Button>
          <Button variant="outline" @click="ReloadData" :disabled="isLoading">
            <RefreshCcw class="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>
    </div>

    <!-- Cluster Grid -->
    <div v-else>
      <div class="mb-4 flex justify-between items-center">
        <p class="text-sm text-muted-foreground">
          Found {{ clusters.total_clusters }} groups with similar faces
        </p>
        <Button variant="outline" size="sm" @click="handleClusterFaces" :disabled="isClustering">
          <RefreshCcw class="mr-2 h-4 w-4" :class="{ 'animate-spin': isClustering }" />
          Re-group Faces
        </Button>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <Card
          v-for="cluster in clusters.clusters"
          :key="cluster.cluster_id"
          class="hover:shadow-lg transition-shadow overflow-hidden"
        >
          <CardContent class="p-0">
            <div class="relative">
              <img
                :src="getPrimaryFaceImageUrl(cluster)"
                alt="Face cluster"
                class="w-full h-48 object-cover cursor-pointer transition-transform duration-150 hover:scale-[1.01]"
                loading="lazy"
                @click="goToCluster(cluster)"
              />
              <Badge class="absolute top-2 right-2 bg-black/60 text-white border-none">
                {{ cluster.face_count }} {{ cluster.face_count === 1 ? 'face' : 'faces' }}
              </Badge>
            </div>
            <div class="p-3 space-y-3">
              <div class="flex items-start justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold leading-tight">
                    {{ cluster.person_name || 'Unlabeled person' }}
                  </p>
                  <p class="text-xs text-muted-foreground">
                    {{ Math.round(cluster.avg_confidence * 100) }}% confidence
                  </p>
                </div>
                <Badge
                  v-if="cluster.person_name"
                  variant="secondary"
                  class="text-[11px] uppercase tracking-wide"
                >
                  Named
                </Badge>
              </div>

              <div class="space-y-2" @click.stop>
                <Input
                  v-model="labelInputs[cluster.cluster_id]"
                  placeholder="Add a name"
                  class="h-9"
                  @keyup.enter="saveLabelForCluster(cluster)"
                />
                <div class="flex items-center gap-2">
                  <Button
                    size="sm"
                    @click="saveLabelForCluster(cluster)"
                    :disabled="isClusterUpdating(cluster.cluster_id) || !canSaveLabelForCluster(cluster)"
                  >
                    <Loader2
                      v-if="isClusterUpdating(cluster.cluster_id)"
                      class="mr-2 h-4 w-4 animate-spin"
                    />
                    <span>Save label</span>
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    class="text-muted-foreground hover:text-foreground"
                    @click="resetLabelForCluster(cluster)"
                    :disabled="isClusterUpdating(cluster.cluster_id)"
                  >
                    Reset
                  </Button>
                </div>
                <p
                  v-if="statusMessages[cluster.cluster_id]"
                  class="text-xs"
                  :class="{
                    'text-red-500': statusMessages[cluster.cluster_id].type === 'error',
                    'text-emerald-600': statusMessages[cluster.cluster_id].type === 'success',
                    'text-muted-foreground': statusMessages[cluster.cluster_id].type === 'info'
                  }"
                >
                  {{ statusMessages[cluster.cluster_id].text }}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <!-- Stats -->
      <div class="mt-6 text-center">
        <p class="text-muted-foreground">
          Showing {{ clusters.total_clusters }} face {{ clusters.total_clusters === 1 ? 'group' : 'groups' }}
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
const { isLoading, isClustering, faceData, clusters, error, updatingFaces } = storeToRefs(faceStore);

const labelInputs = ref({});
const statusMessages = ref({});
const statusTimers = new Map();
const showClusters = ref(true); // Toggle between clusters and individual faces

const initializeLabelInputs = (clusters = []) => {
  const next = clusters.reduce((acc, cluster) => {
    acc[cluster.cluster_id] = cluster.person_name || '';
    return acc;
  }, {});
  labelInputs.value = next;
};

watch(
  clusters,
  (newValue) => {
    if (newValue?.clusters) {
      initializeLabelInputs(newValue.clusters);
    } else {
      labelInputs.value = {};
    }
  },
  { immediate: true }
);

const getFaceImageUrl = (faceId) => `${API_BASE_URL}/api/v2/faces/${faceId}/image`;

const getPrimaryFaceImageUrl = (cluster) => {
  const primaryFace = cluster.primary_face || cluster.sample_faces?.[0];
  return primaryFace ? getFaceImageUrl(primaryFace.id) : '';
};

const isFaceUpdating = (faceId) => Boolean(updatingFaces.value?.[faceId]);

const isClusterUpdating = (clusterId) => {
  // Check if any face in the cluster is being updated
  return Boolean(updatingFaces.value?.[clusterId]);
};

const canSaveLabel = (face) => {
  const currentValue = (labelInputs.value?.[face.id] ?? '').trim();
  const existing = (face.person_name ?? '').trim();
  return currentValue.length > 0 && currentValue !== existing;
};

const canSaveLabelForCluster = (cluster) => {
  const currentValue = (labelInputs.value?.[cluster.cluster_id] ?? '').trim();
  const existing = (cluster.person_name ?? '').trim();
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

const saveLabelForCluster = async (cluster) => {
  const inputValue = labelInputs.value?.[cluster.cluster_id] ?? '';
  const trimmedName = inputValue.trim();

  if (!trimmedName) {
    setStatusMessage(cluster.cluster_id, 'Please enter a name before saving.', 'error');
    return;
  }

  if (!canSaveLabelForCluster(cluster)) {
    setStatusMessage(cluster.cluster_id, 'No changes to save.', 'info');
    return;
  }

  try {
    // Get all face IDs from the cluster's sample faces
    const faceIds = cluster.sample_faces?.map(f => f.id) || [];
    if (faceIds.length === 0) {
      setStatusMessage(cluster.cluster_id, 'No faces found in cluster.', 'error');
      return;
    }

    // Use the store to update the first face (which should update the whole cluster)
    await faceStore.assignPersonToFace(faceIds[0], trimmedName);

    labelInputs.value = {
      ...labelInputs.value,
      [cluster.cluster_id]: trimmedName
    };
    faceStore.clearError();
    setStatusMessage(cluster.cluster_id, 'Label saved for all faces in group.', 'success');

    // Reload clusters to see updated names
    setTimeout(() => ReloadData(), 1500);
  } catch (err) {
    console.error('Failed to assign label to cluster:', err);
    const message = err?.message || 'Failed to save label.';
    setStatusMessage(cluster.cluster_id, message, 'error');
  }
};

const resetLabelForCluster = (cluster) => {
  labelInputs.value = {
    ...labelInputs.value,
    [cluster.cluster_id]: cluster.person_name || ''
  };
  clearStatusMessage(cluster.cluster_id);
};

const handleClusterFaces = async () => {
  try {
    await faceStore.triggerClustering();
    setStatusMessage('clustering', 'Face grouping started! This may take a moment...', 'success');

    // Wait a bit and then reload
    setTimeout(async () => {
      await ReloadData();
    }, 3000);
  } catch (err) {
    console.error('Failed to trigger clustering:', err);
    setStatusMessage('clustering', 'Failed to start face grouping.', 'error');
  }
};

const ReloadData = async () => {
  try {
    await Promise.all([
      faceStore.loadClusters(),
      faceStore.loadFaceData()
    ]);
    console.log('Clusters loaded:', clusters.value);
    console.log('Face data loaded:', faceData.value);
  } catch (err) {
    console.error('Failed to load data:', err);
  }
};

const goToRelatedImages = (faceId) => {
  router.push(`/faces/${faceId}`);
};

const goToCluster = (cluster) => {
  // Navigate to the primary face or first face in cluster
  const primaryFace = cluster.primary_face || cluster.sample_faces?.[0];
  if (primaryFace) {
    router.push(`/faces/${primaryFace.id}`);
  }
};

onMounted(async () => {
  await ReloadData();
});

onBeforeUnmount(() => {
  statusTimers.forEach((timeoutId) => clearTimeout(timeoutId));
  statusTimers.clear();
});
</script>
