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

    <!-- Display files from Firebase -->
    <div v-else class="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <FileCard v-for="file in files" :key="file.name" :file="file" :loading="file.loading" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Dropzone from 'dropzone';
import moment from 'moment';
import { storage } from '../services/firebase';
import { ref as storageRef, getDownloadURL, uploadBytesResumable, listAll } from 'firebase/storage';
import FileCard from '../components/FileCard.vue';

const files = ref([]); // Reactive list to store uploaded files
const selectedFiles = ref([]); // Track files selected by the user for upload
const isLoading = ref(true); // Loading state

// Function to load files from Firebase Storage
const loadFiles = async () => {
  const folderRef = storageRef(storage, 'uploads');
  try {
    const result = await listAll(folderRef);
    const filePromises = result.items.map(async (fileRef) => {
      const url = await getDownloadURL(fileRef);
      return {
        name: fileRef.name,
        url: url,
        loading: false,
        icon: url
      };
    });
    files.value = await Promise.all(filePromises);
  } catch (error) {
    console.error('Error loading files:', error);
  } finally {
    isLoading.value = false;
  }
};

// Function to upload files to Firebase
const uploadToFirebase = async (uploadedFiles) => {
  for (const file of uploadedFiles) {
    console.log(`Uploading file: ${file.name}`);
    const fileRef = storageRef(storage, `uploads/${file.name}`);
    const uploadTask = uploadBytesResumable(fileRef, file);

    // Add the file to the list with a loading state
    files.value.push({
      name: file.name,
      url: '',
      loading: true,
      progress: 0,
      icon: URL.createObjectURL(file)
    });

    // Track upload progress and update UI
    uploadTask.on(
      'state_changed',
      (snapshot) => {
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        const fileIndex = files.value.findIndex(f => f.name === file.name);
        if (fileIndex !== -1) {
          files.value[fileIndex].progress = progress;
        }
      },
      (error) => console.error('Error uploading file to Firebase:', error),
      async () => {
        try {
          const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
          const fileIndex = files.value.findIndex(f => f.name === file.name);
          if (fileIndex !== -1) {
            files.value[fileIndex] = {
              ...files.value[fileIndex],
              url: downloadURL,
              loading: false,
              icon: downloadURL
            };
          }
          // Log the download URL to the console
          console.log(`File uploaded successfully: ${downloadURL}`);
        } catch (error) {
          console.error('Error getting download URL:', error);
        }
      }
    );
  }
};


// Initialize Dropzone
onMounted(() => {
  loadFiles();

  Dropzone.autoDiscover = false;
  const dropzone = new Dropzone("#myDropzone", {
    url: "http://127.0.0.1:5000/serve_images", // Flask endpoint URL
    method: "POST",
    maxFilesize: 5, // Max file size in MB
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
      this.on('successmultiple', (files, response) => {
        if (response.status) {
          uploadToFirebase(files);
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