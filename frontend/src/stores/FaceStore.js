import { defineStore } from 'pinia';
import axios from 'axios';
const apiUrl = import.meta.env.VITE_API_URL;


export const useFaceStore = defineStore('faceStore', {
  state: () => ({
    faceData: null,
    allImages: null,
    isLoading: false,
  }),

  actions: {
    async loadFaceData() {
        // Check if the data is already loaded
        console.log('Loading face data...');
        this.isLoading = true;
        this.faceData = null;
        try {
          const response = await axios.get(`${apiUrl}'/faces/get_faces`);
          this.faceData = response.data; // Store the response in Pinia state
          console.log('Face data loaded successfully');
        } catch (error) {
          console.error('Error fetching face data:', error);
        } finally {
          this.isLoading = false;
        }
    },
    async loadImageData() {
      // Check if the data is already loaded
      console.log('Loading face data...');
      this.isLoading = true;
      this.allImages = null;
      try {
        const response = await axios.get(`${apiUrl}/images/get_images`);
        this.allImages = response.data; // Store the response in Pinia state
        console.log(response.data);
        console.log('Images data loaded successfully');
      } catch (error) {
        console.error('Error fetching face data:', error);
      } finally {
        this.isLoading = false;
      }
    
  }  
  },
});
