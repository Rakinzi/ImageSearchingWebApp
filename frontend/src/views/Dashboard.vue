<template>
  <div class="p-4 dark:bg-gray-900 min-h-screen">
    <h1 class="text-3xl font-bold dark:text-white">My Files</h1>

    <!-- Dropzone Container -->
    <form
      id="dropzone"
      class="dropzone border-dashed border-4 border-gray-500 rounded-lg p-4 mt-4"
    >
      <!-- Only show the dz-message if no files are selected -->
      <div v-if="selectedFiles.length === 0" class="dz-message text-gray-500 dark:text-gray-400">
        Drag and drop image files here or click to upload
      </div>
    </form>

    <!-- Loading Animation for Full Page -->
    <div v-if="isLoading" class="flex items-center justify-center min-h-screen">
      <div class="w-16 h-16 border-4 border-t-4 border-gray-500 border-opacity-50 border-t-transparent rounded-full animate-spin"></div>
    </div>

    <!-- Display files from Firebase -->
    <div v-else class="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <FileCard 
        v-for="file in files" 
        :key="file.name" 
        :file="file" 
        :loading="file.loading"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Dropzone from 'dropzone';
import { storage } from '../services/firebase'; // Adjust path if necessary
import { listAll, ref as storageRef, getDownloadURL, uploadBytesResumable } from 'firebase/storage';
import FileCard from '../components/FileCard.vue'; // Ensure FileCard component exists
import axios from 'axios';

const files = ref([]); // Reactive list to store uploaded files
const selectedFiles = ref([]); // Track files selected by the user for upload
const isLoading = ref(true); // Loading state

// Function to load files from Firebase Storage
const loadFiles = async () => {
  const folderRef = storageRef(storage, 'uploads'); // Folder path in Firebase Storage

  try {
    const result = await listAll(folderRef); // List all files
    const filePromises = result.items.map(async (fileRef) => {
      const url = await getDownloadURL(fileRef); // Get the file URL
      return {
        name: fileRef.name,
        url: url,
        loading: false, // No loading when fetching
        analysis: [], // Placeholder for analysis data
        icon: 'https://via.placeholder.com/50x50.png?text=FILE' // Placeholder icon
      };
    });

    // Resolve all file promises
    files.value = await Promise.all(filePromises);
    console.log('Files loaded from Firebase:', files.value); // Debug log
  } catch (error) {
    console.error('Error loading files:', error);
  } finally {
    isLoading.value = false; // Set loading state to false after loading
  }
};

// Function to upload file to Firebase with progress tracking
const uploadFile = async (file, dropzoneFile) => {
  const fileRef = storageRef(storage, `uploads/${file.name}`);
  const uploadTask = uploadBytesResumable(fileRef, file);

  // Add file to the list with loading state
  const newFile = {
    name: file.name,
    url: '',
    loading: true,
    progress: 0,
    analysis: [], // Placeholder for analysis data
    icon: 'https://via.placeholder.com/50x50.png?text=LOADING', // Placeholder icon
  };

  files.value.push(newFile);

  // Track upload progress
  uploadTask.on(
    'state_changed',
    (snapshot) => {
      const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
      console.log('Upload progress:', progress); // Debug log
      const progressBar = dropzoneFile.previewElement.querySelector('.dz-progress .dz-upload');
      progressBar.style.width = `${progress}%`;
    },
    (error) => {
      console.error('Error uploading file:', error); // Log upload error
      newFile.loading = false; // Mark as not loading on error
    },
    async () => {
      const downloadURL = await getDownloadURL(uploadTask.snapshot.ref);
      console.log('File uploaded successfully:', downloadURL); // Debug log

      // Send file URL and name to the server for MongoDB storage and Clarifai analysis
      try {
        const response = await axios.post('http://localhost:5000/upload', {
          fileUrl: downloadURL,
          fileName: file.name,
        });

        // Update file with analysis results
        const fileIndex = files.value.findIndex(f => f.name === file.name);
        files.value[fileIndex].url = downloadURL;
        files.value[fileIndex].loading = false;
        files.value[fileIndex].analysis = response.data.analysis; // Clarifai analysis data

        // Remove file from Dropzone UI
        dropzoneFile.previewElement.remove();
        selectedFiles.value = selectedFiles.value.filter(f => f.name !== file.name);
      } catch (error) {
        console.error('Error saving file to server:', error);
      }
    }
  );
};

// Initialize Dropzone
onMounted(() => {
  loadFiles();

  const dropzoneElement = document.querySelector('#dropzone');

  // Initialize Dropzone instance
  const dropzone = new Dropzone(dropzoneElement, {
    url: '/', // We won't use Dropzone's upload mechanism
    autoProcessQueue: false, // Disable auto-processing of files
    acceptedFiles: 'image/*', // Accept only image files
    init() {
      this.on('addedfile', (file) => {
        console.log('File added:', file); // Debug log
        selectedFiles.value.push(file); // Add the selected file to the array
        uploadFile(file, file); // Call uploadFile with the dropzone file reference
      });
    },
    previewsContainer: '#dropzone', // Make sure previews appear in the dropzone
    previewTemplate: `
      <div class="dz-preview dz-file-preview">
        <div class="dz-image"><img data-dz-thumbnail /></div>
        <div class="dz-progress">
          <span class="dz-upload" data-dz-uploadprogress style="width: 0%; background-color: #4ade80; height: 5px;"></span>
        </div>
      </div>
    `
  });
});
</script>

<style scoped>
/* Loading spinner style */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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
  background-color: #4ade80; /* Green progress bar */
  height: 5px;
  transition: width 0.3s ease-in-out;
}

.dz-image img {
  width: 100%;
  height: auto;
}
</style>
