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
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div
        class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin">
      </div>
    </div>

     <!-- Display face cards in a responsive grid layout -->
     <div v-if="faceData != null"  class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-6">
    
      <FaceCard
        v-for="(faceImage, index) in faceData.face_images"
        :key="index"
        :faceImage="faceImage"
        :faceId="index"
        @relatedImages="handleRelatedImages" 
      />
      </div>
      <div v-else class="">No Faces Detected</div>

      <!-- Display related images when available -->
    <div v-if="relatedImages.length" class="mt-6">
        <h2 class="text-xl font-bold dark:text-white">Related Images</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6 mt-4">
          <img v-for="(image, index) in relatedImages" :key="index" :src="'http://127.0.0.1:5000/' + image" class="w-full h-auto object-cover" />
        </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Dropzone from 'dropzone';
import moment from 'moment';
import FileCard from '../components/FileCard.vue';
import FaceCard from '../components/FaceCard.vue';
import axios  from 'axios';
import { useRouter } from 'vue-router';

const router = useRouter();

const files = ref([]); // Reactive list to store uploaded files
const selectedFiles = ref([]); // Track files selected by the user for upload
const isLoading = ref(true); // Loading state
const faceData = ref(null); // Variable to store face data from the API
const relatedImages = ref([]);  // To store related images from FaceCard

// Function to fetch face data
const loadFaceData = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:5000/faces/process');
    faceData.value = response.data; // Store the response in faceData
    isLoading.value = false;
    console.log('Face data:', faceData.value); // Log the data to the console
  } catch (error) {
    console.error('Error fetching face data:', error);
  }
};

// Function to load files from Firebase Storage


// Function to handle the related images received from FaceCard
const handleRelatedImages = (data) => {
  console.log('Received related images:', data);
  relatedImages.value = data.related_images;
};



// Initialize Dropzone
onMounted(() => {
  loadFaceData();  // Fetch the initial face data

  Dropzone.autoDiscover = false;
  const dropzone = new Dropzone("#myDropzone", {
    url: "http://127.0.0.1:5000/serve_images", // Flask endpoint URL
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
      this.on('successmultiple', (files, response) => {
        if (response.status) {
          // Wait for 5 seconds before reloading face data
          setTimeout(() => {
            // Reload the component
            router.push('/');
            console.log("5 seconds to reload face data");
          }, 5000); // 5000ms = 5 seconds // 5000ms = 5 seconds
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

