<template>
  <div class="p-4 dark:bg-gray-900 min-h-screen">
    <h1 class="text-3xl font-bold dark:text-white">My Files</h1>
    <div class="mt-4 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      <FileCard v-for="file in files" :key="file.id" :file="file" />
    </div>
    <div class="mt-8">
      <UploadButton />
    </div>
  </div>
</template>

<script setup>
import FileCard from '../components/FileCard.vue';
import UploadButton from '../components/UploadButton.vue';

const files = [
  { id: 1, name: 'Document.pdf', size: '2 MB', icon: 'https://via.placeholder.com/50x50.png?text=PDF' },
  { id: 2, name: 'Image.jpg', size: '5 MB', icon: 'https://via.placeholder.com/50x50.png?text=IMG' },
  { id: 3, name: 'Music.mp3', size: '3 MB', icon: 'https://via.placeholder.com/50x50.png?text=MP3' },
  { id: 4, name: 'Video.mp4', size: '20 MB', icon: 'https://via.placeholder.com/50x50.png?text=VIDEO' },
  { id: 5, name: 'Spreadsheet.xls', size: '1.5 MB', icon: 'https://via.placeholder.com/50x50.png?text=XLS' },
  { id: 6, name: 'Presentation.ppt', size: '4 MB', icon: 'https://via.placeholder.com/50x50.png?text=PPT' },
  { id: 7, name: 'Archive.zip', size: '15 MB', icon: 'https://via.placeholder.com/50x50.png?text=ZIP' },
  { id: 8, name: 'Code.js', size: '500 KB', icon: 'https://via.placeholder.com/50x50.png?text=JS' },
];


</script>

<style scoped>
/* Scoped styles for the dashboard */
</style>
