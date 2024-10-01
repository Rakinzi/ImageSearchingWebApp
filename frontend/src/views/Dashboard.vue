<template>
  <div class="p-4 dark:bg-gray-900 min-h-screen">
    <h1 class="text-3xl font-bold dark:text-white">My Files</h1>

    <!-- Dropzone Container -->
    <form id="myDropzone" class="dropzone border-dashed border-4 border-gray-500 rounded-lg p-4 mt-4">
      <!-- Only show the dz-message if no files are selected -->
      <div v-if="selectedFiles.length === 0" class="dz-message text-gray-500 dark:text-gray-400">
        Drag and drop image files here or click to upload
      </div>
    </form>

    <!-- Loading Animation for Full Page -->
    <div v-if="faceStore.isLoading" class="flex items-center justify-center min-h-screen">
      <div
        class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin">
      </div>
    </div>
     <!-- Image Gallery -->
     <div v-else class="mt-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <div v-for="(image, index) in faceStore.faceData.all_images" :key="index" class="relative">
        <img
          :src="'http://127.0.0.1:5000/' + image"
          :alt="'Image ' + (index + 1)"
          class="w-full h-48 object-cover rounded-lg shadow-md transition-transform transform hover:scale-105"
        />
        <div class="absolute bottom-2 left-2 bg-black bg-opacity-50 text-white text-xs px-2 py-1 rounded">
          Image {{ index + 1 }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Dropzone from 'dropzone';
import moment from 'moment';
import { useFaceStore } from '../stores/faceStore'; // Import Pinia store
import { useRouter } from 'vue-router';

const router = useRouter();
const faceStore = useFaceStore();
const selectedFiles = ref([]); // Track files selected by the user for upload

onMounted(() => {
  Dropzone.autoDiscover = false;
  const dropzone = new Dropzone("#myDropzone", {
    url: "http://127.0.0.1:5000/images/serve_images", // Flask endpoint URL
    method: "POST",
    maxFilesize: 50, // Max file size in MB
    acceptedFiles: 'image/*', // Accept only image files
    autoProcessQueue: true,
    uploadMultiple: true,
    parallelUploads: 100,
    paramName: "image",
    clickable: true,
    init: function () {
      this.on('addedfiles', (files) => {
        selectedFiles.value.push(...files);
      });

      this.on('sendingmultiple', (files, xhr, formData) => {
        let imageDetailsArray = [];
        files.forEach(file => {
          const imageUri = URL.createObjectURL(file);
          const imageType = file.type;
          const filename = file.name;
          const creationDate = moment(file.lastModified).format('YYYY-MM-DD');
          // Collect image details for each file
          imageDetailsArray.push({
            creationDate: creationDate,
            filename: filename,
            uri: imageUri,
            content_type: imageType // Add this field to avoid errors in Flask
          });
        });
        // Append the image details array as a JSON string
        formData.append('image_details', JSON.stringify(imageDetailsArray));
      });

        // Success event for multiple files
      this.on('successmultiple', async (files, response) => {
        if (response.status) {
          try {
            // Clear face data
            faceStore.faceData = null;
            console.log(faceStore.faceData)
            // Load face data from the store
            await faceStore.loadFaceData();
            console.log(faceStore.faceData)
            // Redirect to the '/people' route after loading the data
            // router.push('/people');
            console.log("Face data loaded successfully, redirected to /people");
          } catch (error) {
            console.error('Error loading face data:', error);
          }
        } else {
          console.error('Error uploading files to server:', response.message);
        }
      });


      this.on('errormultiple', (files, errorMessage) => {
        console.error('Error uploading files:', errorMessage);
      });
    },
    previewTemplate: `
      <div class="dz-preview dz-file-preview">
        <div class="dz-image"><img data-dz-thumbnail /></div>
        <div class="dz-progress"><span class="dz-upload" data-dz-uploadprogress></span></div>
        <div class="dz-error-message"><span data-dz-errormessage></span></div>
      </div>
    `
  });
});
</script>

<style scoped>
/* Loading spinner style */
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.w-16 {
  width: 4rem;
}

.h-16 {
  height: 4rem;
}

.border-4 {
  border-width: 4px;
}

.border-t-4 {
  border-top-width: 4px;
}

.border-gray-500 {
  border-color: #6b7280;
}

.border-opacity-50 {
  border-opacity: 0.5;
}

.border-t-transparent {
  border-top-color: transparent;
}

.rounded-full {
  border-radius: 9999px;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

.dropzone {
  min-height: 150px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.dz-message {
  font-size: 1.2rem;
}

.dz-progress {
  width: 100%;
  background-color: #f3f4f6;
  border-radius: 5px;
  margin-top: 0.5rem;
}

.dz-upload {
  background-color: #4ade80;
  /* Green progress bar */
  height: 5px;
  transition: width 0.3s ease-in-out;
}

.dz-image img {
  width: 100%;
  height: auto;
}
</style>

