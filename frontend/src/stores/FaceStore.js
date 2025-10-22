import { defineStore } from 'pinia';
import { apiService, handleApiError } from '../services/api.js';


export const useFaceStore = defineStore('faceStore', {
  state: () => ({
    faceData: null,
    allImages: null,
    isLoading: false,
    error: null,
  }),

  actions: {
    async loadFaceData() {
      console.log('Loading face data...');
      this.isLoading = true;
      this.faceData = null;
      this.error = null;

      try {
        const response = await apiService.faces.list();
        this.faceData = response.data;
        console.log('Face data loaded successfully');
      } catch (error) {
        console.error('Error fetching face data:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
      } finally {
        this.isLoading = false;
      }
    },

    async loadImageData() {
      console.log('Loading image data...');
      this.isLoading = true;
      this.allImages = null;
      this.error = null;

      try {
        const response = await apiService.images.list();
        this.allImages = response.data; // Store the response in Pinia state
        console.log('Images data loaded successfully');
      } catch (error) {
        console.error('Error fetching images data:', error);
        const errorInfo = handleApiError(error);
        this.error = errorInfo.message;
      } finally {
        this.isLoading = false;
      }
    },

    clearError() {
      this.error = null;
    }
  },
});
